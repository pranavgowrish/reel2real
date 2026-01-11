from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Tuple
from urllib.parse import quote_plus
from itinerary_algorithm import Location, build_itinerary
from location_services import (
    search_location, 
    calculate_travel_time_matrix, 
    get_opening_hours,
    get_location_data_by_name,
    find_restaurant_near_hotel,
    find_restaurant_near_location,
    TEST_LOCATIONS,
    TEST_CASES
)

app = FastAPI(title="Itinerary Builder API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class LocationInput(BaseModel):
    name: str
    open_time: int = Field(..., alias="openTime")
    close_time: int = Field(..., alias="closeTime")
    duration: int
    priority: Optional[int] = None  # Optional - deprecated, not used in cost calculation (algorithm optimizes purely on travel time + waiting time)

    class Config:
        populate_by_name = True


class LocationWithCoordsInput(BaseModel):
    name: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    address: Optional[str] = None


class ItineraryRequest(BaseModel):
    locations: List[LocationInput]
    travel_time: List[List[int]] = Field(..., alias="travelTime")
    start_idx: int = Field(..., alias="startIdx")
    start_time: int = Field(..., alias="startTime")
    location_coords: Optional[List[LocationWithCoordsInput]] = Field(None, alias="locationCoords")

    class Config:
        populate_by_name = True


class ItineraryResponse(BaseModel):
    route: List[str]
    route_indices: List[int]
    end_time: int
    google_maps_url: Optional[str] = None
    meal_times: Optional[dict] = None
    hotel_location: Optional[str] = None


class LocationSearchResult(BaseModel):
    name: str
    address: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    type: Optional[str] = None
    place_id: Optional[str] = None


class LocationWithCoords(BaseModel):
    name: str
    lat: float
    lon: float
    openTime: Optional[int] = None
    closeTime: Optional[int] = None
    duration: Optional[int] = None
    priority: Optional[int] = None


class TravelTimeMatrixRequest(BaseModel):
    locations: List[LocationWithCoords]


@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "message": "Itinerary Builder API",
        "status": "running",
        "docs": "Visit http://localhost:8000/docs for API documentation",
        "frontend": "React frontend should be running on http://localhost:3000",
        "endpoints": {
            "health": "/api/health",
            "build_itinerary": "POST /api/build-itinerary"
        }
    }


def generate_google_maps_url(
    route_indices: List[int], 
    location_coords: List[LocationWithCoordsInput],
    route_names: List[str]
) -> Optional[str]:
    """
    Generate a Google Maps directions URL for the route.
    Uses coordinates if available, otherwise uses location names.
    """
    if not route_indices or not location_coords:
        return None
    
    waypoints = []
    all_lats = []
    all_lons = []
    
    # Build waypoints in route order
    for idx in route_indices:
        if idx < len(location_coords):
            loc = location_coords[idx]
            if loc.lat is not None and loc.lon is not None:
                # Use coordinates for accuracy (preferred method)
                waypoints.append(f"{loc.lat},{loc.lon}")
                all_lats.append(loc.lat)
                all_lons.append(loc.lon)
            elif loc.address:
                # Use name + address if available
                waypoint = f"{loc.name}, {loc.address}"
                waypoints.append(quote_plus(waypoint))
            else:
                # Fallback to name only
                waypoints.append(quote_plus(loc.name))
        elif idx < len(route_names):
            # Fallback to route name from algorithm result
            waypoints.append(quote_plus(route_names[idx]))
        else:
            # Last resort: generic location name
            waypoints.append(quote_plus(f"Location {idx}"))
    
    if not waypoints:
        return None
    
    # Build Google Maps URL
    # Format: https://www.google.com/maps/dir/waypoint1/waypoint2/waypoint3/...
    base_url = "https://www.google.com/maps/dir/"
    url = base_url + "/".join(waypoints)
    
    # Add map center and zoom if we have coordinates for better view
    if all_lats and all_lons:
        avg_lat = sum(all_lats) / len(all_lats)
        avg_lon = sum(all_lons) / len(all_lons)
        url += f"/@{avg_lat},{avg_lon},13z"
    
    return url


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


@app.get("/api/search-location")
async def search_location_api(
    query: str = Query(..., min_length=2),
    category: Optional[str] = Query(None, description="Filter by category: restaurant, hotel, etc.")
):
    """
    Search for locations by name/address.
    Uses Nominatim (OpenStreetMap) or Geoapify if API key is set.
    Optional category filter: 'restaurant', 'hotel', etc.
    """
    try:
        results = await search_location(query)
        
        # Filter by category if provided
        if category:
            category_lower = category.lower()
            filtered_results = []
            for result in results:
                name_lower = result.get("name", "").lower()
                type_lower = result.get("type", "").lower()
                address_lower = result.get("address", "").lower()
                
                if category_lower == "restaurant":
                    # Look for restaurant keywords
                    is_match = (
                        "restaurant" in name_lower or
                        "cafe" in name_lower or
                        "café" in name_lower or
                        "bistro" in name_lower or
                        "eatery" in name_lower or
                        "food" in name_lower or
                        "dining" in name_lower or
                        "restaurant" in type_lower
                    )
                elif category_lower == "hotel":
                    is_match = (
                        "hotel" in name_lower or
                        "hotel" in type_lower or
                        "hotel" in address_lower
                    )
                else:
                    is_match = category_lower in name_lower or category_lower in type_lower
                
                if is_match:
                    filtered_results.append(result)
            results = filtered_results
        
        return [LocationSearchResult(**result) for result in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching location: {str(e)}")


@app.post("/api/calculate-travel-matrix")
async def calculate_travel_matrix_api(request: TravelTimeMatrixRequest):
    """
    Calculate travel time matrix between locations using their coordinates.
    Returns matrix in minutes.
    """
    try:
        if len(request.locations) < 2:
            raise HTTPException(status_code=400, detail="At least 2 locations required")
        
        coordinates = [(loc.lat, loc.lon) for loc in request.locations]
        matrix = await calculate_travel_time_matrix(coordinates)
        
        return {
            "matrix": matrix,
            "locations": [loc.name for loc in request.locations]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating travel matrix: {str(e)}")


@app.get("/api/get-opening-hours")
async def get_opening_hours_api(
    lat: float = Query(...),
    lon: float = Query(...),
    name: str = Query(...)
):
    """
    Get opening hours for a location from OpenStreetMap.
    Returns (open_time, close_time) in minutes from midnight.
    """
    try:
        open_time, close_time = await get_opening_hours(lat, lon, name)
        return {
            "openTime": open_time,
            "closeTime": close_time,
            "openTimeFormatted": f"{open_time // 60:02d}:{open_time % 60:02d}",
            "closeTimeFormatted": f"{close_time // 60:02d}:{close_time % 60:02d}"
        }
    except Exception as e:
        # Return defaults if error
        return {
            "openTime": 540,  # 9 AM default
            "closeTime": 1260,  # 9 PM default
            "openTimeFormatted": "09:00",
            "closeTimeFormatted": "21:00",
            "note": f"Using defaults (error: {str(e)})"
        }


@app.get("/api/find-nearby-restaurant")
async def find_nearby_restaurant_api(
    lat: float = Query(...),
    lon: float = Query(...),
    radius: int = Query(1000, description="Search radius in meters (default 1000m = 1km)")
):
    """
    Find nearby restaurants around a given location.
    Useful for finding lunch spots during the 12-3 PM window.
    """
    try:
        # Search for restaurants near the coordinates
        query = f"restaurant near {lat},{lon}"
        results = await search_location(query, limit=10)
        
        # Filter for restaurants and calculate distances
        restaurants = []
        for result in results:
            if result.get("lat") and result.get("lon"):
                name_lower = result.get("name", "").lower()
                is_restaurant = (
                    "restaurant" in name_lower or
                    "cafe" in name_lower or
                    "café" in name_lower or
                    "bistro" in name_lower or
                    "eatery" in name_lower
                )
                if is_restaurant:
                    # Calculate distance (simple haversine)
                    import math
                    lat1, lon1 = math.radians(lat), math.radians(lon)
                    lat2, lon2 = math.radians(result["lat"]), math.radians(result["lon"])
                    dlat = lat2 - lat1
                    dlon = lon2 - lon1
                    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                    c = 2 * math.asin(math.sqrt(a))
                    distance_m = 6371000 * c  # Earth radius in meters
                    
                    if distance_m <= radius:
                        restaurants.append({
                            **result,
                            "distance_meters": int(distance_m),
                            "distance_km": round(distance_m / 1000, 2)
                        })
        
        # Sort by distance
        restaurants.sort(key=lambda x: x.get("distance_meters", float('inf')))
        
        return restaurants[:5]  # Return top 5 closest
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding restaurants: {str(e)}")


@app.get("/api/test-case")
async def get_test_case(city: str = Query("new_york", description="Test case city: new_york, las_vegas, paris, san_francisco, los_angeles")):
    """
    Get a pre-configured test case with real locations for a specified city.
    Fetches address, coordinates, and opening hours from OpenStreetMap dynamically.
    
    Available test cases:
    - new_york: New York City landmarks
    - las_vegas: Las Vegas Strip and attractions
    - paris: Paris, France landmarks
    - san_francisco: San Francisco attractions
    - los_angeles: Los Angeles attractions
    """
    try:
        from location_services import get_location_data_by_name, TEST_CASES
        
        # Get the test case for the specified city
        if city not in TEST_CASES:
            raise HTTPException(status_code=400, detail=f"Unknown test case: {city}. Available: {', '.join(TEST_CASES.keys())}")
        
        test_case = TEST_CASES[city]
        CITY_NAME = test_case["city"]
        default_lat = test_case["default_lat"]
        default_lon = test_case["default_lon"]
        test_locations = test_case["locations"]
        
        # Fetch location data from OSM for each test location
        locations_data = []
        for loc in test_locations:
            location_data = await get_location_data_by_name(loc["name"], city=CITY_NAME)
            
            if location_data:
                # Merge with user preferences (duration only - priority removed)
                formatted_loc = {
                    "name": location_data["name"],
                    "address": location_data.get("address", ""),
                    "lat": location_data["lat"],
                    "lon": location_data["lon"],
                    "open_time": location_data.get("open_time", 540),  # Default 9 AM
                    "close_time": location_data.get("close_time", 1260),  # Default 9 PM
                    "duration": loc["duration"],
                    "priority": None  # Not used in cost calculation
                }
                locations_data.append(formatted_loc)
            else:
                # Fallback if OSM lookup fails - use defaults
                formatted_loc = {
                    "name": loc["name"],
                    "address": "",
                    "lat": default_lat,
                    "lon": default_lon,
                    "open_time": 540 if "hotel" not in loc["name"].lower() else 0,
                    "close_time": 1260 if "hotel" not in loc["name"].lower() else 1440,
                    "duration": loc["duration"],
                    "priority": None  # Not used in cost calculation
                }
                locations_data.append(formatted_loc)
        
        # Get coordinates from fetched locations
        coordinates = [(loc["lat"], loc["lon"]) for loc in locations_data]
        
        # Calculate travel time matrix
        matrix = await calculate_travel_time_matrix(coordinates)
        
        return {
            "locations": locations_data,
            "travelTimeMatrix": matrix,
            "startIdx": 0,
            "startTime": 540,  # 9:00 AM
            "city": city,
            "city_name": CITY_NAME
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating test case: {str(e)}")


@app.get("/api/test-cases")
async def list_test_cases():
    """
    List all available test cases.
    """
    try:
        from location_services import TEST_CASES
        return {
            "test_cases": {
                key: {
                    "city": value["city"],
                    "location_count": len(value["locations"])
                }
                for key, value in TEST_CASES.items()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing test cases: {str(e)}")


@app.post("/api/build-itinerary", response_model=ItineraryResponse)
async def build_itinerary_api(request: ItineraryRequest):
    """
    Build an itinerary based on locations, travel times, and starting parameters.
    """
    try:
        # Validate input
        n = len(request.locations)
        if n == 0:
            raise HTTPException(status_code=400, detail="At least one location is required")
        
        if len(request.travel_time) != n:
            raise HTTPException(
                status_code=400, 
                detail=f"Travel time matrix must have {n} rows (got {len(request.travel_time)})"
            )
        
        for i, row in enumerate(request.travel_time):
            if len(row) != n:
                raise HTTPException(
                    status_code=400,
                    detail=f"Travel time matrix row {i} must have {n} columns (got {len(row)})"
                )
        
        if request.start_idx < 0 or request.start_idx >= n:
            raise HTTPException(
                status_code=400,
                detail=f"Start index must be between 0 and {n-1} (got {request.start_idx})"
            )
        
        # Convert input locations to Location objects
        locations = [
            Location(
                loc.name,
                loc.open_time,
                loc.close_time,
                loc.duration,
                loc.priority if loc.priority is not None else 1  # Default for backward compatibility
            )
            for loc in request.locations
        ]
        
        # Build itinerary WITHOUT restaurant locations - we'll find them dynamically
        # Don't return to hotel yet - we'll add dinner restaurant first
        result = build_itinerary(
            locations,
            request.travel_time,
            request.start_idx,
            request.start_time,
            return_to_hotel=False,  # We'll handle return to hotel after dinner
            lunch_window=(720, 900),  # 12:00 PM - 3:00 PM
            lunch_duration=60,  # 1 hour lunch
            restaurant_locations=[]  # No restaurants in the list - find them dynamically
        )
        route_indices, end_time, meal_times = result
        
        # Clear any meal_times that might have been set by the algorithm (we'll set them properly)
        if 'dinner_location' in meal_times and meal_times['dinner_location'] == request.start_idx:
            del meal_times['dinner_location']
            del meal_times['dinner_time']
        
        # Now process the route and dynamically add restaurants
        # Track current time as we go through the route
        current_time = request.start_time
        final_route_indices = [route_indices[0]]  # Start with hotel
        current_idx = route_indices[0]
        lunch_taken = False
        lunch_restaurant = None
        
        # Go through the route and check for lunch opportunities after finishing each location
        for i in range(1, len(route_indices)):
            idx = route_indices[i]
            
            # Calculate travel time to this location
            # If we're at a lunch restaurant (marked as -2), calculate distance manually
            if current_idx == -2 and lunch_restaurant:
                # Calculate travel from lunch restaurant to next location
                import math
                if request.location_coords and len(request.location_coords) > idx:
                    next_loc_coords = request.location_coords[idx]
                    if next_loc_coords.lat and next_loc_coords.lon:
                        lat1, lon1 = math.radians(lunch_restaurant["lat"]), math.radians(lunch_restaurant["lon"])
                        lat2, lon2 = math.radians(next_loc_coords.lat), math.radians(next_loc_coords.lon)
                        dlat = lat2 - lat1
                        dlon = lon2 - lon1
                        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                        c = 2 * math.asin(math.sqrt(a))
                        distance_km = 6371 * c
                        travel = max(1, int(distance_km * 1.2))
                    else:
                        travel = 10  # Default fallback
                else:
                    travel = 10  # Default fallback
            else:
                travel = request.travel_time[current_idx][idx] if current_idx >= 0 else 10
            arrival = current_time + travel
            
            # Check if we arrive before opening time
            if arrival < locations[idx].open:
                arrival = locations[idx].open
            
            # Check BEFORE visiting if we should take lunch (if we're approaching lunch time)
            lunch_start, lunch_end_window = 720, 900
            should_take_lunch_before = False
            
            if not lunch_taken:
                # Estimate finish time for this location
                finish_time_estimate = arrival + locations[idx].duration
                
                # Take lunch BEFORE visiting if we're approaching or in lunch time
                # Check multiple conditions to be more aggressive about finding lunch
                if (current_time >= 660 or  # 11:00 AM or later - more aggressive
                    finish_time_estimate >= lunch_start or  # Will finish after 12 PM
                    lunch_start <= arrival <= lunch_end_window or  # Arriving during lunch window
                    (current_time < lunch_start and lunch_start - current_time <= 60)):  # Within 1 hour of lunch
                    should_take_lunch_before = True
            
            if should_take_lunch_before:
                # Find restaurant near CURRENT location (where we are now, before visiting next location)
                search_lat = None
                search_lon = None
                
                # Use current location coordinates (where we are now)
                if current_idx >= 0 and request.location_coords and len(request.location_coords) > current_idx:
                    current_loc_coords = request.location_coords[current_idx]
                    if current_loc_coords.lat and current_loc_coords.lon:
                        search_lat = current_loc_coords.lat
                        search_lon = current_loc_coords.lon
                # Fallback: if we don't have current location coords, use the next location's coords
                elif request.location_coords and len(request.location_coords) > idx:
                    next_loc_coords = request.location_coords[idx]
                    if next_loc_coords.lat and next_loc_coords.lon:
                        search_lat = next_loc_coords.lat
                        search_lon = next_loc_coords.lon
                
                # Always try to find a restaurant (function has fallback, so it will always return something)
                if search_lat and search_lon:
                    lunch_restaurant = await find_restaurant_near_location(search_lat, search_lon, radius_m=2000)
                else:
                    # If we don't have coordinates, use a default location (hotel coordinates as fallback)
                    if request.location_coords and len(request.location_coords) > request.start_idx:
                        hotel_coords = request.location_coords[request.start_idx]
                        if hotel_coords.lat and hotel_coords.lon:
                            lunch_restaurant = await find_restaurant_near_location(hotel_coords.lat, hotel_coords.lon, radius_m=2000)
                
                if lunch_restaurant:
                        # Calculate travel time to lunch restaurant from current position
                        import math
                        lat1, lon1 = math.radians(search_lat), math.radians(search_lon)
                        lat2, lon2 = math.radians(lunch_restaurant["lat"]), math.radians(lunch_restaurant["lon"])
                        dlat = lat2 - lat1
                        dlon = lon2 - lon1
                        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                        c = 2 * math.asin(math.sqrt(a))
                        distance_km = 6371 * c
                        travel_to_lunch = max(1, int(distance_km * 1.2))
                        
                        # Add lunch restaurant to route
                        final_route_indices.append(-2)  # Special marker for lunch restaurant
                        
                        # Update time: travel to lunch, lunch duration (60 min)
                        lunch_arrival = current_time + travel_to_lunch
                        if lunch_arrival < lunch_start:
                            lunch_arrival = lunch_start
                        lunch_end = lunch_arrival + 60
                        
                        current_time = lunch_end
                        current_idx = -2  # Mark that we're at lunch restaurant
                        
                        meal_times['lunch_time'] = lunch_arrival
                        meal_times['lunch_location'] = lunch_restaurant["name"]
                        meal_times['lunch_address'] = lunch_restaurant.get("address", "")
                        lunch_taken = True
                        
                        # After lunch, we still need to visit the location (idx)
                        # Calculate travel from lunch restaurant to the location
                        if request.location_coords and len(request.location_coords) > idx:
                            next_loc_coords = request.location_coords[idx]
                            if next_loc_coords.lat and next_loc_coords.lon:
                                lat1, lon1 = math.radians(lunch_restaurant["lat"]), math.radians(lunch_restaurant["lon"])
                                lat2, lon2 = math.radians(next_loc_coords.lat), math.radians(next_loc_coords.lon)
                                dlat = lat2 - lat1
                                dlon = lon2 - lon1
                                a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                                c = 2 * math.asin(math.sqrt(a))
                                distance_km = 6371 * c
                                travel_from_lunch = max(1, int(distance_km * 1.2))
                                
                                # Visit the location after lunch
                                arrival_from_lunch = current_time + travel_from_lunch
                                if arrival_from_lunch < locations[idx].open:
                                    arrival_from_lunch = locations[idx].open
                                finish_from_lunch = arrival_from_lunch + locations[idx].duration
                                
                                # Add the location to route
                                final_route_indices.append(idx)
                                
                                current_time = finish_from_lunch
                                current_idx = idx
                                continue  # Skip the normal visit logic below
                        
                        # If we couldn't calculate travel from lunch, fall through to normal visit
                        continue
            
            # Visit the location (normal case - no lunch before)
            finish_time = arrival + locations[idx].duration
            
            # Also check AFTER visiting if we finished during lunch window (late lunch catch-up)
            if not lunch_taken and lunch_start <= finish_time <= lunch_end_window:
                # Find restaurant near this location (we just finished visiting it)
                if request.location_coords and len(request.location_coords) > idx:
                    loc_coords = request.location_coords[idx]
                    if loc_coords.lat and loc_coords.lon:
                        lunch_restaurant = await find_restaurant_near_location(loc_coords.lat, loc_coords.lon, radius_m=2000)  # Increased radius
                        # The function always returns a restaurant (has fallback), so proceed if we got a result
                        if lunch_restaurant:
                            # Add the location first
                            final_route_indices.append(idx)
                            
                            # Calculate travel time to lunch restaurant
                            import math
                            lat1, lon1 = math.radians(loc_coords.lat), math.radians(loc_coords.lon)
                            lat2, lon2 = math.radians(lunch_restaurant["lat"]), math.radians(lunch_restaurant["lon"])
                            dlat = lat2 - lat1
                            dlon = lon2 - lon1
                            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                            c = 2 * math.asin(math.sqrt(a))
                            distance_km = 6371 * c
                            travel_to_lunch = max(1, int(distance_km * 1.2))
                            
                            # Add lunch restaurant to route
                            final_route_indices.append(-2)  # Special marker for lunch restaurant
                            
                            # Update time: travel to lunch, lunch duration (60 min)
                            lunch_arrival = finish_time + travel_to_lunch
                            if lunch_arrival < lunch_start:
                                lunch_arrival = lunch_start
                            lunch_end = lunch_arrival + 60
                            
                            current_time = lunch_end
                            current_idx = -2  # Mark that we're at lunch restaurant
                            
                            meal_times['lunch_time'] = lunch_arrival
                            meal_times['lunch_location'] = lunch_restaurant["name"]
                            meal_times['lunch_address'] = lunch_restaurant.get("address", "")
                            lunch_taken = True
                            
                            # Next location will be calculated from lunch restaurant position
                            continue
            
            # Add the current location (if we didn't already add it for lunch)
            if final_route_indices[-1] != idx:
                final_route_indices.append(idx)
            
            current_time = finish_time
            current_idx = idx
        
        # Now handle dinner: find restaurant near last location if it's around 7-8 PM
        dinner_restaurant = None
        dinner_time_set = False
        if final_route_indices and len(final_route_indices) > 0:
            # Find the last actual location (skip restaurant markers)
            last_location_idx = None
            for i in range(len(final_route_indices) - 1, -1, -1):
                if final_route_indices[i] >= 0:
                    last_location_idx = final_route_indices[i]
                    break
            
            if last_location_idx is not None and last_location_idx != request.start_idx:
                if request.location_coords and len(request.location_coords) > last_location_idx:
                    last_loc_coords = request.location_coords[last_location_idx]
                    if last_loc_coords.lat and last_loc_coords.lon:
                        # Always try to find dinner restaurant near last location
                        # Target dinner around 7-8 PM (1260-1320), but be flexible
                        dinner_restaurant = await find_restaurant_near_location(
                            last_loc_coords.lat, 
                            last_loc_coords.lon, 
                            radius_m=2000  # Increased radius
                        )
                        
                        # The function should always return something (has fallback), so proceed if we got a result
                        if dinner_restaurant:
                            # Add dinner restaurant
                            final_route_indices.append(-1)  # Special marker for dinner restaurant
                            
                            # Calculate travel times
                            import math
                            lat1, lon1 = math.radians(last_loc_coords.lat), math.radians(last_loc_coords.lon)
                            lat2, lon2 = math.radians(dinner_restaurant["lat"]), math.radians(dinner_restaurant["lon"])
                            dlat = lat2 - lat1
                            dlon = lon2 - lon1
                            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                            c = 2 * math.asin(math.sqrt(a))
                            distance_km = 6371 * c
                            travel_to_dinner = max(1, int(distance_km * 1.2))
                            
                            dinner_start = current_time + travel_to_dinner
                            # Target dinner around 7-8 PM (1260-1320), but be flexible
                            # If we finish between 6-7 PM, aim for 7 PM. Otherwise proceed immediately.
                            if 1140 <= current_time < 1260 and dinner_start < 1260:
                                dinner_start = 1260  # Aim for 7 PM if we're finishing around 6-7 PM
                            
                            dinner_end = dinner_start + 60  # 1 hour dinner
                            
                            # Travel from dinner restaurant to hotel
                            hotel_coords = request.location_coords[request.start_idx]
                            if hotel_coords.lat and hotel_coords.lon:
                                lat_hotel, lon_hotel = math.radians(hotel_coords.lat), math.radians(hotel_coords.lon)
                                dlat = lat_hotel - lat2
                                dlon = lon_hotel - lon2
                                a = math.sin(dlat/2)**2 + math.cos(lat2) * math.cos(lat_hotel) * math.sin(dlon/2)**2
                                c = 2 * math.asin(math.sqrt(a))
                                distance_km = 6371 * c
                                travel_to_hotel = max(1, int(distance_km * 1.2))
                                
                                end_time = dinner_end + travel_to_hotel
                                meal_times['dinner_time'] = dinner_start
                                meal_times['dinner_location'] = dinner_restaurant["name"]
                                meal_times['dinner_address'] = dinner_restaurant.get("address", "")
                                dinner_time_set = True
                            else:
                                end_time = dinner_end
                                meal_times['dinner_time'] = dinner_start
                                meal_times['dinner_location'] = dinner_restaurant["name"]
                                meal_times['dinner_address'] = dinner_restaurant.get("address", "")
                                dinner_time_set = True
            
            # If no dinner restaurant was found, calculate travel to hotel
            if not dinner_time_set:
                if last_location_idx is not None and last_location_idx != request.start_idx:
                    hotel_coords = request.location_coords[request.start_idx]
                    if hotel_coords.lat and hotel_coords.lon:
                        import math
                        if request.location_coords and len(request.location_coords) > last_location_idx:
                            last_loc_coords = request.location_coords[last_location_idx]
                            if last_loc_coords.lat and last_loc_coords.lon:
                                lat1, lon1 = math.radians(last_loc_coords.lat), math.radians(last_loc_coords.lon)
                                lat2, lon2 = math.radians(hotel_coords.lat), math.radians(hotel_coords.lon)
                                dlat = lat2 - lat1
                                dlon = lon2 - lon1
                                a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                                c = 2 * math.asin(math.sqrt(a))
                                distance_km = 6371 * c
                                travel_to_hotel = max(1, int(distance_km * 1.2))
                                end_time = current_time + travel_to_hotel
                            else:
                                end_time = current_time
                        else:
                            end_time = current_time
                    else:
                        end_time = current_time
                else:
                    end_time = current_time
        
        # Add hotel at the end if not already there
        # If dinner restaurant was added, hotel comes after it. Otherwise, hotel comes after last location.
        if final_route_indices and final_route_indices[-1] != request.start_idx:
            # Check if dinner restaurant was already added (marker -1)
            if final_route_indices[-1] == -1:
                # Dinner restaurant is last, so add hotel after it
                final_route_indices.append(request.start_idx)
            elif not dinner_time_set:
                # No dinner restaurant, calculate travel to hotel from last location
                last_idx = final_route_indices[-1]
                if last_idx >= 0 and request.location_coords and len(request.location_coords) > last_idx:
                    last_loc_coords = request.location_coords[last_idx]
                    if last_loc_coords.lat and last_loc_coords.lon:
                        hotel_coords = request.location_coords[request.start_idx]
                        if hotel_coords.lat and hotel_coords.lon:
                            import math
                            lat1, lon1 = math.radians(last_loc_coords.lat), math.radians(last_loc_coords.lon)
                            lat2, lon2 = math.radians(hotel_coords.lat), math.radians(hotel_coords.lon)
                            dlat = lat2 - lat1
                            dlon = lon2 - lon1
                            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                            c = 2 * math.asin(math.sqrt(a))
                            distance_km = 6371 * c
                            travel_to_hotel = max(1, int(distance_km * 1.2))
                            if 'end_time' not in locals() or end_time is None:
                                end_time = current_time + travel_to_hotel
                            else:
                                end_time = max(end_time, current_time + travel_to_hotel)
                
                final_route_indices.append(request.start_idx)
            else:
                # Dinner was set, hotel should already be added after dinner restaurant
                # But if it's not there, add it
                if final_route_indices[-1] != request.start_idx:
                    final_route_indices.append(request.start_idx)
        
        route_indices = final_route_indices
        
        # Convert route indices to location names, handling restaurant markers
        route_names = []
        for idx in route_indices:
            if idx == -2:  # Lunch restaurant marker
                if lunch_restaurant:
                    route_names.append(lunch_restaurant["name"])
            elif idx == -1:  # Dinner restaurant marker
                if dinner_restaurant:
                    route_names.append(dinner_restaurant["name"])
            elif 0 <= idx < len(locations):
                route_names.append(locations[idx].name)
        
        # Generate Google Maps URL if coordinates are available
        google_maps_url = None
        if request.location_coords and len(request.location_coords) > 0:
            # Build waypoints for Google Maps URL, handling restaurant markers
            waypoints = []
            all_lats = []
            all_lons = []
            
            for idx in route_indices:
                if idx == -2:  # Lunch restaurant marker
                    if lunch_restaurant:
                        lat = lunch_restaurant["lat"]
                        lon = lunch_restaurant["lon"]
                        waypoints.append(f"{lat},{lon}")
                        all_lats.append(lat)
                        all_lons.append(lon)
                elif idx == -1:  # Dinner restaurant marker
                    if dinner_restaurant:
                        lat = dinner_restaurant["lat"]
                        lon = dinner_restaurant["lon"]
                        waypoints.append(f"{lat},{lon}")
                        all_lats.append(lat)
                        all_lons.append(lon)
                elif 0 <= idx < len(request.location_coords):
                    loc = request.location_coords[idx]
                    if loc.lat is not None and loc.lon is not None:
                        waypoints.append(f"{loc.lat},{loc.lon}")
                        all_lats.append(loc.lat)
                        all_lons.append(loc.lon)
                    elif loc.address:
                        waypoint = f"{loc.name}, {loc.address}"
                        waypoints.append(quote_plus(waypoint))
                    else:
                        waypoints.append(quote_plus(loc.name))
            
            if waypoints:
                base_url = "https://www.google.com/maps/dir/"
                url = base_url + "/".join(waypoints)
                
                # Add map center and zoom if we have coordinates
                if all_lats and all_lons:
                    avg_lat = sum(all_lats) / len(all_lats)
                    avg_lon = sum(all_lons) / len(all_lons)
                    url += f"/@{avg_lat},{avg_lon},14z"
                
                google_maps_url = url
        
        # Convert meal times to response format (locations are already names)
        meal_info = {}
        if meal_times:
            if 'lunch_time' in meal_times:
                meal_info['lunch_time'] = meal_times['lunch_time']
                if 'lunch_location' in meal_times:
                    meal_info['lunch_location'] = meal_times['lunch_location']
                if 'lunch_address' in meal_times:
                    meal_info['lunch_address'] = meal_times['lunch_address']
            if 'dinner_time' in meal_times:
                meal_info['dinner_time'] = meal_times['dinner_time']
                if 'dinner_location' in meal_times:
                    meal_info['dinner_location'] = meal_times['dinner_location']
                if 'dinner_address' in meal_times:
                    meal_info['dinner_address'] = meal_times['dinner_address']
        
        return ItineraryResponse(
            route=route_names,
            route_indices=route_indices,
            end_time=end_time,
            google_maps_url=google_maps_url,
            meal_times=meal_info if meal_info else None,
            hotel_location=locations[request.start_idx].name
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building itinerary: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
