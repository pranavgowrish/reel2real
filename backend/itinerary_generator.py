"""
Complete itinerary generator that takes location names and returns a full itinerary.
Combines location search, travel time calculation, and route optimization.
"""

import asyncio
from typing import List, Dict, Optional
from location_services import (
    get_location_data_by_name,
    calculate_travel_time_matrix,
    find_restaurant_near_location
)
from itinerary_algorithm import Location, build_itinerary


def format_time_12hr(minutes: int) -> str:
    """Convert minutes from midnight to 12-hour format string."""
    hours = minutes // 60
    mins = minutes % 60
    period = "AM" if hours < 12 else "PM"
    display_hour = hours if hours <= 12 else hours - 12
    if display_hour == 0:
        display_hour = 12
    return f"{display_hour}:{mins:02d} {period}"


def format_duration(minutes: int) -> str:
    """Format duration in minutes to human-readable string."""
    if minutes < 60:
        return f"{minutes} minutes"
    hours = minutes // 60
    mins = minutes % 60
    if mins == 0:
        return f"{hours} hour{'s' if hours > 1 else ''}"
    return f"{hours} hour{'s' if hours > 1 else ''} {mins} minutes"


def can_visit_location(arrival_time: int, duration: int, open_time: int, close_time: int) -> bool:
    """Check if a location can be visited within its opening hours."""
    # If open 24/7 (open_time=0, close_time=1440), always visitable
    if open_time == 0 and close_time == 1440:
        return True
    
    # Check if we can arrive after opening and finish before closing
    earliest_start = max(arrival_time, open_time)
    departure_time = earliest_start + duration
    
    return departure_time <= close_time


async def generate_itinerary(
    location_names: List[str],
    city: str = "Paris, France",
    start_time_minutes: int = 540,  # 9:00 AM default
    include_lunch: bool = True,
    include_dinner: bool = True
) -> Dict:
    """
    Generate a complete itinerary from a list of location names.
    
    Args:
        location_names: List of location names (e.g., ["Eiffel Tower", "Louvre Museum"])
        city: City name for location search context (e.g., "Paris, France")
        start_time_minutes: Starting time in minutes from midnight (540 = 9:00 AM)
        include_lunch: Whether to automatically add lunch
        include_dinner: Whether to automatically add dinner
    
    Returns:
        Dictionary with complete itinerary including coordinates, times, and details
    """
    
    # Step 1: Fetch location data from OpenStreetMap
    print(f"Fetching location data for {len(location_names)} locations...")
    locations_data = []
    
    for name in location_names:
        location_data = await get_location_data_by_name(name, city=city)
        
        if location_data:
            # Use default duration based on location type
            duration = 60  # Default 1 hour
            name_lower = name.lower()
            
            # Adjust duration based on location type
            if any(word in name_lower for word in ["museum", "gallery"]):
                duration = 180  # 3 hours for museums
            elif any(word in name_lower for word in ["tower", "monument"]):
                duration = 90  # 1.5 hours for towers/monuments
            elif any(word in name_lower for word in ["park", "garden", "canyon", "dam"]):
                duration = 120  # 2 hours for parks/outdoor attractions
            
            locations_data.append({
                "name": location_data["name"],
                "address": location_data.get("address", ""),
                "lat": location_data["lat"],
                "lon": location_data["lon"],
                "open_time": location_data.get("open_time", 540),
                "close_time": location_data.get("close_time", 1260),
                "duration": duration
            })
        else:
            print(f"Warning: Could not find location data for '{name}'")
            continue
    
    if not locations_data:
        raise ValueError("No valid locations found")
    
    # Step 2: Calculate travel time matrix
    print("Calculating travel times...")
    coordinates = [(loc["lat"], loc["lon"]) for loc in locations_data]
    travel_matrix = await calculate_travel_time_matrix(coordinates)
    
    # Step 3: Build Location objects for algorithm
    locations = [
        Location(
            loc["name"],
            loc["open_time"],
            loc["close_time"],
            loc["duration"],
            priority=1  # Not used in cost calculation
        )
        for loc in locations_data
    ]
    
    # Step 4: Run itinerary optimization algorithm
    print("Optimizing route...")
    route_indices, end_time, meal_times = build_itinerary(
        locations,
        travel_matrix,
        0,  # Starting index (not used as hotel anymore)
        start_time_minutes,
        return_to_hotel=False,
        lunch_window=(720, 900),  # 12:00 PM - 3:00 PM
        lunch_duration=60,
        restaurant_locations=[]
    )
    
    # Step 5: Build itinerary with meal locations
    itinerary_items = []
    current_time = start_time_minutes
    lunch_added = False
    item_id = 1
    skipped_locations = []
    
    # Track coordinates for mapping (avoid duplicates)
    waypoint_coords = []
    seen_coords = set()
    
    for i, idx in enumerate(route_indices):
        loc_data = locations_data[idx]
        loc = locations[idx]
        
        # Calculate arrival time
        if i > 0:
            prev_idx = route_indices[i - 1]
            travel_time = travel_matrix[prev_idx][idx]
            current_time += travel_time
        
        # Check if location can be visited within opening hours
        if not can_visit_location(current_time, loc.duration, loc.open, loc.close):
            # Try waiting until opening time
            if current_time < loc.open:
                # Wait for opening
                wait_time = loc.open - current_time
                if wait_time <= 120:  # Only wait up to 2 hours
                    current_time = loc.open
                else:
                    # Too long to wait, skip this location
                    skipped_locations.append({
                        "name": loc.name,
                        "reason": f"Would arrive at {format_time_12hr(current_time)}, opens at {format_time_12hr(loc.open)} ({wait_time} min wait)"
                    })
                    continue
            else:
                # Would arrive after closing or can't finish before closing
                departure_time = current_time + loc.duration
                skipped_locations.append({
                    "name": loc.name,
                    "reason": f"Would close at {format_time_12hr(loc.close)}, needs {format_duration(loc.duration)} visit"
                })
                continue
        
        # Wait for opening if necessary (already validated above)
        if current_time < loc.open:
            current_time = loc.open
        
        # Check if we should add lunch before this location
        if include_lunch and not lunch_added and 660 <= current_time <= 900:
            # Find restaurant near current or previous location
            search_lat = loc_data["lat"]
            search_lon = loc_data["lon"]
            
            lunch_restaurant = await find_restaurant_near_location(
                search_lat, search_lon, radius_m=2000
            )
            
            if lunch_restaurant:
                # Check if restaurant is open for lunch
                restaurant_open = lunch_restaurant.get("open_time", 720)
                restaurant_close = lunch_restaurant.get("close_time", 1320)
                
                # Adjust lunch time if restaurant isn't open yet
                lunch_time = max(current_time, restaurant_open)
                
                if lunch_time + 60 <= restaurant_close:  # Can finish lunch before closing
                    lunch_coord_key = (round(lunch_restaurant["lat"], 6), round(lunch_restaurant["lon"], 6))
                    
                    itinerary_items.append({
                        "id": str(item_id),
                        "name": lunch_restaurant["name"],
                        "time": format_time_12hr(lunch_time),
                        "duration": "1 hour",
                        "address": lunch_restaurant.get("address", ""),
                        "openingHours": f"{format_time_12hr(restaurant_open)} - {format_time_12hr(restaurant_close)}",
                        "tags": ["Lunch"],
                        "websiteUrl": None,
                        "isMeal": "lunch",
                        "lat": lunch_restaurant["lat"],
                        "lon": lunch_restaurant["lon"]
                    })
                    
                    if lunch_coord_key not in seen_coords:
                        waypoint_coords.append({
                            "lat": lunch_restaurant["lat"],
                            "lng": lunch_restaurant["lon"]
                        })
                        seen_coords.add(lunch_coord_key)
                    
                    item_id += 1
                    current_time = lunch_time + 60
                    lunch_added = True
        
        # Add the location to itinerary
        tags = []
        
        # Determine tags based on location type
        name_lower = loc.name.lower()
        if any(word in name_lower for word in ["museum", "gallery"]):
            tags.append("Cultural")
        elif any(word in name_lower for word in ["tower", "monument"]):
            tags.append("Landmark")
        elif any(word in name_lower for word in ["park", "garden", "canyon", "recreation"]):
            tags.append("Nature")
        
        itinerary_items.append({
            "id": str(item_id),
            "name": loc.name,
            "time": format_time_12hr(current_time),
            "duration": format_duration(loc.duration),
            "address": loc_data["address"],
            "openingHours": f"{format_time_12hr(loc.open)} - {format_time_12hr(loc.close)}",
            "tags": tags,
            "websiteUrl": None,
            "isMeal": None,
            "lat": loc_data["lat"],
            "lon": loc_data["lon"]
        })
        
        coord_key = (round(loc_data["lat"], 6), round(loc_data["lon"], 6))
        if coord_key not in seen_coords:
            waypoint_coords.append({
                "lat": loc_data["lat"],
                "lng": loc_data["lon"]
            })
            seen_coords.add(coord_key)
        
        item_id += 1
        current_time += loc.duration
    
    # Step 6: Add dinner at the end
    dinner_location_name = None
    dinner_location_address = None
    
    if include_dinner and len(itinerary_items) > 0:
        # Find the last location's coordinates
        last_item = itinerary_items[-1]
        
        dinner_restaurant = await find_restaurant_near_location(
            last_item["lat"], last_item["lon"], radius_m=2000
        )
        
        if dinner_restaurant:
            restaurant_open = dinner_restaurant.get("open_time", 1080)  # 6 PM default
            restaurant_close = dinner_restaurant.get("close_time", 1320)  # 10 PM default
            
            # Aim for dinner around 7-8 PM, but respect restaurant hours
            dinner_time = current_time
            if dinner_time < 1140:  # Before 7 PM
                dinner_time = max(1140, restaurant_open)  # 7 PM or when restaurant opens
            else:
                # If arriving later, use current time if restaurant is still open
                dinner_time = max(dinner_time, restaurant_open)
            
            # Only add dinner if restaurant is open
            if dinner_time + 60 <= restaurant_close:
                dinner_location_name = dinner_restaurant["name"]
                dinner_location_address = dinner_restaurant.get("address", "")
                
                itinerary_items.append({
                    "id": str(item_id),
                    "name": dinner_restaurant["name"],
                    "time": format_time_12hr(dinner_time),
                    "duration": "1 hour",
                    "address": dinner_location_address,
                    "openingHours": f"{format_time_12hr(restaurant_open)} - {format_time_12hr(restaurant_close)}",
                    "tags": ["Dinner"],
                    "websiteUrl": None,
                    "isMeal": "dinner",
                    "lat": dinner_restaurant["lat"],
                    "lon": dinner_restaurant["lon"]
                })
                
                dinner_coord_key = (round(dinner_restaurant["lat"], 6), round(dinner_restaurant["lon"], 6))
                if dinner_coord_key not in seen_coords:
                    waypoint_coords.append({
                        "lat": dinner_restaurant["lat"],
                        "lng": dinner_restaurant["lon"]
                    })
                    seen_coords.add(dinner_coord_key)
                
                current_time = dinner_time + 60
    
    # Step 7: Build final response
    if not itinerary_items:
        raise ValueError("No locations could be added to the itinerary within opening hours")
    
    first_item = itinerary_items[0]
    last_waypoint = waypoint_coords[-1] if waypoint_coords else {"lat": first_item["lat"], "lng": first_item["lon"]}
    
    # Remove origin and destination from waypoints (they shouldn't be in the middle points)
    origin_coord = (round(first_item["lat"], 6), round(first_item["lon"], 6))
    dest_coord = (round(last_waypoint["lat"], 6), round(last_waypoint["lng"], 6))
    
    filtered_waypoints = [
        wp for wp in waypoint_coords
        if (round(wp["lat"], 6), round(wp["lng"], 6)) != origin_coord
        and (round(wp["lat"], 6), round(wp["lng"], 6)) != dest_coord
    ]
    
    result = {
        "itinerary": itinerary_items,
        "images": [],  # Could be populated with image search API
        "videos": [],  # Could be populated with YouTube API
        "coordinates": {
            "origin": {
                "lat": first_item["lat"],
                "lng": first_item["lon"]
            },
            "destination": last_waypoint,
            "waypoints": filtered_waypoints
        },
        "summary": {
            "total_locations": len(itinerary_items),
            "start_time": format_time_12hr(start_time_minutes),
            "end_time": format_time_12hr(current_time),
            "duration": format_duration(current_time - start_time_minutes)
        },
        "last_location": {
            "name": dinner_location_name,
            "address": dinner_location_address
        }
    }
    
    # Add warnings about skipped locations if any
    if skipped_locations:
        result["warnings"] = {
            "skipped_locations": skipped_locations
        }
        print("\n⚠️  WARNING: Some locations were skipped due to opening hours:")
        for skip in skipped_locations:
            print(f"   - {skip['name']}: {skip['reason']}")
    
    return result


# Example usage
async def main():
    """Example usage of the itinerary generator."""
    
    # Example: Paris itinerary
    location_names = [
        "Eiffel Tower",
        "Louvre Museum",
        "Notre-Dame de Paris",
        "Arc de Triomphe"
    ]
    
    print("Generating itinerary for Paris...")
    itinerary = await generate_itinerary(
        location_names,
        city="Paris, France",
        start_time_minutes=540  # 9:00 AM
    )
    
    print("\n=== ITINERARY ===")
    for item in itinerary["itinerary"]:
        meal_tag = f" [{item['isMeal'].upper()}]" if item['isMeal'] else ""
        print(f"{item['id']}. {item['name']}{meal_tag}")
        print(f"   Time: {item['time']} ({item['duration']})")
        print(f"   Opening Hours: {item['openingHours']}")
        print(f"   Address: {item['address']}")
        print()
    
    print(f"\n=== SUMMARY ===")
    print(f"Total locations: {itinerary['summary']['total_locations']}")
    print(f"Start: {itinerary['summary']['start_time']}")
    print(f"End: {itinerary['summary']['end_time']}")
    print(f"Total duration: {itinerary['summary']['duration']}")
    
    if itinerary['last_location']['name']:
        print(f"\n=== LAST LOCATION ===")
        print(f"Name: {itinerary['last_location']['name']}")
        print(f"Address: {itinerary['last_location']['address']}")


if __name__ == "__main__":
    asyncio.run(main())