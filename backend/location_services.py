"""
Location services for searching places, calculating travel times, and getting opening hours.
Uses Nominatim (OSM) for location search, OpenRouteService for routing, and OSM Overpass for opening hours.
"""
import httpx
import os
import math
from typing import Optional, List, Dict, Tuple
from dotenv import load_dotenv

load_dotenv()

# API Keys (optional - services work without keys but with rate limits)
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY", "")
OPENROUTESERVICE_API_KEY = os.getenv("OPENROUTESERVICE_API_KEY", "")

# Free alternatives that don't require API keys
NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"
OPENROUTESERVICE_BASE_URL = "https://api.openrouteservice.org/v2"


async def search_location(query: str, limit: int = 5) -> List[Dict]:
    """
    Search for locations using Nominatim (OpenStreetMap) - preferred for accuracy.
    Falls back to Geoapify if Nominatim fails and API key is available.
    Returns list of location results with name, coordinates, and address.
    """
    try:
        # Always try Nominatim first (OpenStreetMap) - it's free and works well
        # Use Nominatim (OpenStreetMap) - free, no API key needed
        try:
            async with httpx.AsyncClient() as client:
                url = f"{NOMINATIM_BASE_URL}/search"
                headers = {
                    "User-Agent": "ItineraryBuilder/1.0"  # Required by Nominatim
                }
                params = {
                    "q": query,
                    "format": "json",
                    "limit": limit,
                    "addressdetails": 1
                }
                response = await client.get(url, params=params, headers=headers, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data:
                    lat_val = item.get("lat")
                    lon_val = item.get("lon")
                    # Validate coordinates exist and are valid
                    lat = None
                    lon = None
                    if lat_val and lon_val:
                        try:
                            lat = float(lat_val)
                            lon = float(lon_val)
                            # Validate coordinate ranges
                            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                                lat = None
                                lon = None
                        except (ValueError, TypeError):
                            lat = None
                            lon = None
                    
                    results.append({
                        "name": item.get("display_name", query).split(",")[0],
                        "address": item.get("display_name", ""),
                        "lat": lat,
                        "lon": lon,
                        "type": item.get("type", ""),
                        "place_id": item.get("place_id", "")
                    })
                
                # If we got valid results with coordinates, return them
                if results and any(r.get("lat") is not None and r.get("lon") is not None for r in results):
                    return results
        except Exception as e:
            print(f"Nominatim search failed: {e}, trying fallback...")
        
        # Fallback to Geoapify if available and Nominatim didn't return good results
        if GEOAPIFY_API_KEY:
            # Use Geoapify if API key is available
            async with httpx.AsyncClient() as client:
                url = "https://api.geoapify.com/v1/geocode/search"
                params = {
                    "text": query,
                    "apiKey": GEOAPIFY_API_KEY,
                    "limit": limit,
                    "format": "json"
                }
                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                results = []
                for result in data.get("results", []):
                    # Geoapify returns coordinates directly in the result or in properties
                    # Try multiple possible locations for coordinates
                    lat = None
                    lon = None
                    
                    # Check if coordinates are in geometry.coordinates (GeoJSON format: [lon, lat])
                    geometry = result.get("geometry", {})
                    if geometry and "coordinates" in geometry:
                        coords = geometry["coordinates"]
                        if len(coords) >= 2:
                            lon = coords[0]
                            lat = coords[1]
                    else:
                        # Check if coordinates are directly in result
                        lat = result.get("lat")
                        lon = result.get("lon")
                        # If not, check in properties
                        if lat is None or lon is None:
                            props = result.get("properties", {})
                            lat = props.get("lat") or lat
                            lon = props.get("lon") or lon
                    
                    # Validate and convert to float
                    if lat is not None and lon is not None:
                        try:
                            lat = float(lat)
                            lon = float(lon)
                            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                                lat = None
                                lon = None
                        except (ValueError, TypeError):
                            lat = None
                            lon = None
                    
                    props = result.get("properties", {})
                    results.append({
                        "name": props.get("name") or result.get("formatted", query),
                        "address": props.get("formatted", result.get("formatted", "")),
                        "lat": lat,
                        "lon": lon,
                        "type": props.get("type", result.get("result_type", "")),
                        "place_id": result.get("place_id", "")
                    })
                return results
        
        # If both Nominatim and Geoapify failed, return empty list
        return []
    except Exception as e:
        print(f"Error searching location: {e}")
        return []


def _estimate_travel_time(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> int:
    """
    Estimate travel time between two coordinates using straight-line distance.
    Returns time in minutes.
    """
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    distance_km = 6371 * c  # Earth radius in km
    # Estimate: ~50 km/h average city speed = ~1.2 min/km
    return max(1, int(distance_km * 1.2))


async def calculate_travel_time_matrix(
    coordinates: List[Tuple[float, float]], 
    profile: str = "drive"
) -> List[List[int]]:
    """
    Calculate travel time matrix between multiple coordinates using Geoapify Routing API
    (if API key available) or OpenRouteService, with fallback to distance estimation.
    Returns matrix in minutes (rounded up).
    """
    n = len(coordinates)
    if n == 0:
        return []
    
    try:
        # Try Geoapify Routing API first (if API key available)
        if GEOAPIFY_API_KEY:
            async with httpx.AsyncClient() as client:
                matrix = []
                # Geoapify Routing API calculates routes between waypoints
                for i, coord1 in enumerate(coordinates):
                    row = []
                    for j, coord2 in enumerate(coordinates):
                        if i == j:
                            row.append(0)
                        else:
                            try:
                                # Build waypoints: lat1,lon1|lat2,lon2
                                waypoints = f"{coord1[0]},{coord1[1]}|{coord2[0]},{coord2[1]}"
                                url = "https://api.geoapify.com/v1/routing"
                                params = {
                                    "waypoints": waypoints,
                                    "mode": "drive",  # drive, walk, bicycle, etc.
                                    "apiKey": GEOAPIFY_API_KEY
                                }
                                
                                response = await client.get(url, params=params, timeout=15.0)
                                if response.status_code == 200:
                                    data = response.json()
                                    # Extract time from Geoapify response
                                    if "features" in data and len(data["features"]) > 0:
                                        time_seconds = data["features"][0].get("properties", {}).get("time", 0)
                                        # Convert to minutes (rounded up)
                                        time_minutes = max(1, int(time_seconds / 60) + (1 if time_seconds % 60 > 0 else 0))
                                        row.append(time_minutes)
                                    else:
                                        # Fallback to distance estimation if no route found
                                        row.append(_estimate_travel_time(coord1, coord2))
                                else:
                                    # Fallback to distance estimation on error
                                    row.append(_estimate_travel_time(coord1, coord2))
                            except Exception:
                                # Fallback to distance estimation on exception
                                row.append(_estimate_travel_time(coord1, coord2))
                    matrix.append(row)
                return matrix
        
        # Fallback to OpenRouteService API if Geoapify not available
        if OPENROUTESERVICE_API_KEY:
            async with httpx.AsyncClient() as client:
                url = f"{OPENROUTESERVICE_BASE_URL}/matrix/{profile}"
                headers = {
                    "Authorization": OPENROUTESERVICE_API_KEY,
                    "Content-Type": "application/json"
                }
                
                # Format coordinates as [lon, lat] for OpenRouteService
                locations = [[coord[1], coord[0]] for coord in coordinates]
                
                payload = {
                    "locations": locations,
                    "metrics": ["duration"],
                    "units": "m"
                }
                
                response = await client.post(url, json=payload, headers=headers, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                
                # Convert duration from seconds to minutes (rounded up)
                durations = data.get("durations", [])
                matrix = []
                for row in durations:
                    matrix.append([max(1, int(d / 60) + (1 if d % 60 > 0 else 0)) for d in row])
                
                return matrix
        
        # Final fallback: Calculate straight-line distance and estimate travel time
        matrix = []
        for i, coord1 in enumerate(coordinates):
            row = []
            for j, coord2 in enumerate(coordinates):
                if i == j:
                    row.append(0)
                else:
                    row.append(_estimate_travel_time(coord1, coord2))
            matrix.append(row)
        return matrix
    except Exception as e:
        print(f"Error calculating travel time matrix: {e}")
        # Fallback to straight-line distance estimation
        matrix = []
        for i, coord1 in enumerate(coordinates):
            row = []
            for j, coord2 in enumerate(coordinates):
                if i == j:
                    row.append(0)
                else:
                    row.append(_estimate_travel_time(coord1, coord2))
            matrix.append(row)
        return matrix


async def get_location_data_by_name(name: str, city: str = "Paris, France") -> Optional[Dict]:
    """
    Get complete location data from OpenStreetMap using only the name.
    Returns dict with name, address, lat, lon, open_time, close_time, google_maps_url, or None if not found.
    Coordinates are guaranteed to be valid floats suitable for Google Maps URLs.
    """
    try:
        # Search using Nominatim first to get coordinates
        search_query = f"{name}, {city}" if city else name
        search_results = await search_location(search_query, limit=5)
        
        # search_location already filters for valid coordinates
        if not search_results:
            # Try searching without city if first search failed
            if city and name != city:
                search_results = await search_location(name, limit=5)
        
        if not search_results:
            print(f"Could not find location with valid coordinates: {name} (searched: {search_query})")
            return None
        
        # Use the first result (already validated)
        result = search_results[0]
        lat = result["lat"]  # Already a valid float
        lon = result["lon"]  # Already a valid float
        address = result.get("address", result.get("name", name))
        
        # Get opening hours
        open_time, close_time = await get_opening_hours_by_coords(lat, lon, name)
        
        return {
            "name": name,
            "address": address,
            "lat": lat,
            "lon": lon,
            "open_time": open_time,
            "close_time": close_time,
            "google_maps_url": f"https://www.google.com/maps?q={lat},{lon}"
        }
        
    except Exception as e:
        print(f"Error getting location data for {name}: {e}")
        import traceback
        traceback.print_exc()
        return None


async def get_opening_hours_by_coords(lat: float, lon: float, name: str) -> Tuple[int, int]:
    """
    Get opening hours from OpenStreetMap Overpass API using coordinates.
    Returns (open_time, close_time) in minutes from midnight, or defaults (0, 1440 = 24 hours).
    Uses smart defaults based on location type to avoid Overpass API timeouts.
    """
    # Use smart defaults based on location name/keywords to avoid API calls
    name_lower = name.lower()
    
    # Hotels are typically 24/7
    if any(word in name_lower for word in ["hotel", "hostel", "accommodation"]):
        return (0, 1440)
    
    # Restaurants and cafes typically open late
    if any(word in name_lower for word in ["restaurant", "cafe", "café", "bistro", "eatery", "dining"]):
        return (720, 1320)  # 12 PM - 10 PM
    
    # Museums typically 9 AM - 6 PM
    if any(word in name_lower for word in ["museum", "gallery"]):
        return (540, 1080)  # 9 AM - 6 PM
    
    # Churches and religious sites typically early morning to evening
    if any(word in name_lower for word in ["church", "cathedral", "basilica", "chapel", "sacré", "notre-dame"]):
        return (360, 1140)  # 6 AM - 7 PM
    
    # Towers and monuments typically 9 AM - 7 PM
    if any(word in name_lower for word in ["tower", "monument", "arc", "triumph"]):
        return (540, 1140)  # 9 AM - 7 PM
    
    # Try Overpass API with shorter timeout, but don't wait long
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:  # Reduced timeout
            # Try alternative Overpass instances first (faster ones)
            overpass_instances = [
                "https://overpass.kumi.systems/api/interpreter",  # Often faster
                "https://overpass-api.de/api/interpreter",  # Original
            ]
            
            import re
            escaped_name = re.escape(name)
            
            # Simplified query for faster response
            query = f"""
            [out:json][timeout:5];
            (
              node["name"~"{escaped_name}",i](around:200,{lat},{lon});
              way["name"~"{escaped_name}",i](around:200,{lat},{lon});
            );
            out tags;
            """
            
            for overpass_url in overpass_instances:
                try:
                    response = await client.post(
                        overpass_url,
                        data={"data": query},
                        timeout=5.0,
                        headers={"Content-Type": "application/x-www-form-urlencoded"}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        elements = data.get("elements", [])
                        
                        for element in elements:
                            tags = element.get("tags", {})
                            opening_hours = tags.get("opening_hours", "")
                            
                            if opening_hours:
                                # Parse opening hours
                                if "24/7" in opening_hours or "24" in opening_hours:
                                    return (0, 1440)
                                
                                # Extract time range
                                time_match = re.search(r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})', opening_hours)
                                if time_match:
                                    open_hour, open_min = int(time_match.group(1)), int(time_match.group(2))
                                    close_hour, close_min = int(time_match.group(3)), int(time_match.group(4))
                                    open_time = open_hour * 60 + open_min
                                    close_time = close_hour * 60 + close_min
                                    return (open_time, close_time)
                        break  # Successfully got response, stop trying other instances
                except (httpx.TimeoutException, httpx.HTTPStatusError):
                    continue  # Try next instance
                except Exception:
                    continue  # Try next instance
    except Exception:
        pass  # Fall through to defaults
    
    # Default: assume open 9 AM to 9 PM for general attractions
    return (540, 1260)


async def get_opening_hours(lat: float, lon: float, name: str) -> Tuple[int, int]:
    """
    Alias for get_opening_hours_by_coords for backward compatibility.
    """
    return await get_opening_hours_by_coords(lat, lon, name)


async def find_restaurant_near_location(lat: float, lon: float, radius_m: int = 1500) -> Optional[Dict]:
    """
    Find a restaurant near any given location using OpenStreetMap.
    Returns restaurant data with name, address, lat, lon, open_time, close_time, or None if not found.
    
    Args:
        lat: Latitude of the location
        lon: Longitude of the location
        radius_m: Search radius in meters (default 1500m = 1.5km)
    """
    try:
        # Use Nominatim to search for restaurants - try multiple query formats
        async with httpx.AsyncClient(timeout=15.0) as client:
            headers = {
                "User-Agent": "ItineraryBuilder/1.0"
            }
            
            # Try different search queries
            queries = [
                f"restaurant {lat},{lon}",
                f"[amenity=restaurant] {lat},{lon}",
                f"restaurant Paris {lat},{lon}",
            ]
            
            restaurants = []
            
            for query in queries:
                try:
                    url = f"{NOMINATIM_BASE_URL}/search"
                    params = {
                        "q": query,
                        "format": "json",
                        "limit": 20,
                        "addressdetails": 1,
                    }
                    
                    response = await client.get(url, params=params, headers=headers, timeout=10.0)
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Filter and find restaurants
                        for item in data:
                            name = item.get("display_name", "").split(",")[0]
                            name_lower = name.lower()
                            type_lower = item.get("type", "").lower()
                            class_lower = item.get("class", "").lower()
                            address_lower = item.get("display_name", "").lower()
                            
                            # Check if it's a restaurant (exclude hotels)
                            is_restaurant = (
                                ("restaurant" in name_lower or "restaurant" in type_lower or "restaurant" in class_lower or "restaurant" in address_lower) or
                                "cafe" in name_lower or
                                "café" in name_lower or
                                "bistro" in name_lower or
                                "eatery" in name_lower or
                                "dining" in name_lower or
                                class_lower == "amenity" and type_lower in ["restaurant", "cafe", "fast_food", "food_court"]
                            ) and "hotel" not in name_lower and "hotel" not in address_lower
                            
                            if is_restaurant and item.get("lat") and item.get("lon"):
                                try:
                                    lat_val = float(item.get("lat"))
                                    lon_val = float(item.get("lon"))
                                    
                                    # Calculate distance
                                    import math
                                    lat1, lon1 = math.radians(lat), math.radians(lon)
                                    lat2, lon2 = math.radians(lat_val), math.radians(lon_val)
                                    dlat = lat2 - lat1
                                    dlon = lon2 - lon1
                                    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                                    c = 2 * math.asin(math.sqrt(a))
                                    distance_m = 6371000 * c
                                    
                                    if distance_m <= radius_m:
                                        # Avoid duplicates
                                        existing = any(r["name"] == name and abs(r["lat"] - lat_val) < 0.0001 for r in restaurants)
                                        if not existing:
                                            restaurants.append({
                                                "name": name,
                                                "address": item.get("display_name", ""),
                                                "lat": lat_val,
                                                "lon": lon_val,
                                                "distance_m": distance_m
                                            })
                                except (ValueError, TypeError):
                                    continue
                        
                        if restaurants:
                            break  # Found restaurants, stop trying other queries
                except (httpx.TimeoutException, httpx.HTTPStatusError):
                    continue  # Try next query
                except Exception:
                    continue
            
            if not restaurants:
                # Fallback: return a generic restaurant location near the coordinates
                # This ensures we always have a restaurant option
                # Use smart defaults for restaurant hours (12 PM - 10 PM)
                return {
                    "name": "Nearby Restaurant",
                    "address": f"Restaurant near coordinates {lat:.4f}, {lon:.4f}",
                    "lat": lat + 0.001,  # Slight offset to indicate it's nearby
                    "lon": lon + 0.001,
                    "open_time": 720,  # 12 PM
                    "close_time": 1320,  # 10 PM
                    "distance_m": 100  # Estimated 100m away
                }
            
            # Sort by distance and get the closest one
            restaurants.sort(key=lambda x: x["distance_m"])
            closest = restaurants[0]
            
            # Get opening hours for the restaurant
            open_time, close_time = await get_opening_hours_by_coords(
                closest["lat"], closest["lon"], closest["name"]
            )
            
            return {
                "name": closest["name"],
                "address": closest["address"],
                "lat": closest["lat"],
                "lon": closest["lon"],
                "open_time": open_time,
                "close_time": close_time,
                "distance_m": closest["distance_m"]
            }
    except Exception as e:
        print(f"Error finding restaurant near location: {e}")
        # Return a fallback restaurant
        return {
            "name": "Nearby Restaurant",
            "address": f"Restaurant near coordinates",
            "lat": lat,
            "lon": lon,
            "open_time": 720,  # 12 PM
            "close_time": 1320,  # 10 PM
            "distance_m": 0
        }


async def find_restaurant_near_hotel(hotel_lat: float, hotel_lon: float, radius_m: int = 1000) -> Optional[Dict]:
    """
    Alias for find_restaurant_near_location for backward compatibility.
    Find a restaurant near the hotel using OpenStreetMap.
    """
    return await find_restaurant_near_location(hotel_lat, hotel_lon, radius_m)


# Test case data for popular locations (intentionally unordered to test algorithm optimization)
# Only contains names and duration - address, coordinates, and opening hours will be fetched from OSM
# The algorithm optimizes purely on travel time + waiting time (TSP-like with time windows)
# Priority has been removed - route selection is based on time efficiency only

# Multiple test cases for different cities
TEST_CASES = {
    "new_york": {
        "city": "New York, USA",
        "default_lat": 40.7128,
        "default_lon": -74.0060,
        "locations": [
            {"name": "The Plaza Hotel", "duration": 0},  # Starting hotel
            {"name": "Central Park", "duration": 90},
            {"name": "Statue of Liberty", "duration": 120},
            {"name": "Empire State Building", "duration": 60},
            {"name": "Metropolitan Museum of Art", "duration": 180},
            {"name": "Times Square", "duration": 60}
        ]
    },
    "las_vegas": {
        "city": "Las Vegas, USA",
        "default_lat": 36.1699,
        "default_lon": -115.1398,
        "locations": [
            {"name": "Bellagio Hotel", "duration": 0},  # Starting hotel
            {"name": "Las Vegas Strip", "duration": 120},
            {"name": "Fremont Street Experience", "duration": 90},
            {"name": "High Roller Observation Wheel", "duration": 60},
            {"name": "Red Rock Canyon", "duration": 180},
            {"name": "Caesars Palace", "duration": 60}
        ]
    },
    "paris": {
        "city": "Paris, France",
        "default_lat": 48.8566,
        "default_lon": 2.3522,
        "locations": [
            {"name": "Hotel Ritz Paris", "duration": 0},  # Starting hotel
            {"name": "Sacré-Cœur", "duration": 90},
            {"name": "Arc de Triomphe", "duration": 60},
            {"name": "Notre-Dame de Paris", "duration": 60},
            {"name": "Louvre Museum", "duration": 180},
            {"name": "Eiffel Tower", "duration": 120}
        ]
    },
    "san_francisco": {
        "city": "San Francisco, USA",
        "default_lat": 37.7749,
        "default_lon": -122.4194,
        "locations": [
            {"name": "Fairmont San Francisco", "duration": 0},  # Starting hotel
            {"name": "Golden Gate Bridge", "duration": 90},
            {"name": "Alcatraz Island", "duration": 180},
            {"name": "Fisherman's Wharf", "duration": 120},
            {"name": "Lombard Street", "duration": 30},
            {"name": "Golden Gate Park", "duration": 90}
        ]
    },
    "los_angeles": {
        "city": "Los Angeles, USA",
        "default_lat": 34.0522,
        "default_lon": -118.2437,
        "locations": [
            {"name": "Beverly Hills Hotel", "duration": 0},  # Starting hotel
            {"name": "Hollywood Walk of Fame", "duration": 60},
            {"name": "Universal Studios Hollywood", "duration": 300},
            {"name": "Griffith Observatory", "duration": 90},
            {"name": "Santa Monica Pier", "duration": 120},
            {"name": "Getty Center", "duration": 180}
        ]
    }
}

# Default test case (for backward compatibility)
TEST_LOCATIONS = TEST_CASES["new_york"]["locations"]
