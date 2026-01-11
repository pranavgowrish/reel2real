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


async def generate_itinerary(
    location_names: List[str],
    city: str = "Paris, France",
    start_time_minutes: int = 540,  # 9:00 AM default
    hotel_index: int = 0,  # First location is hotel by default
    include_lunch: bool = True,
    include_dinner: bool = True
) -> Dict:
    """
    Generate a complete itinerary from a list of location names.
    
    Args:
        location_names: List of location names (e.g., ["Eiffel Tower", "Louvre Museum"])
        city: City name for location search context (e.g., "Paris, France")
        start_time_minutes: Starting time in minutes from midnight (540 = 9:00 AM)
        hotel_index: Index of the hotel in the location list (default 0)
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
            duration = 120  # Default 1 hour
            name_lower = name.lower()
            
            # Adjust duration based on location type
            # if any(word in name_lower for word in ["museum", "gallery"]):
            #     duration = 180  # 3 hours for museums
            # elif any(word in name_lower for word in ["tower", "monument"]):
            #     duration = 90  # 1.5 hours for towers/monuments
            # elif any(word in name_lower for word in ["park", "garden"]):
            #     duration = 120  # 2 hours for parks
            if any(word in name_lower for word in ["hotel", "hostel"]):
                duration = 0  # No duration for hotel

            
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
        hotel_index,
        start_time_minutes,
        return_to_hotel=False,  # We'll handle meals and hotel return manually
        lunch_window=(720, 900),  # 12:00 PM - 3:00 PM
        lunch_duration=90,
        restaurant_locations=[]
    )
    
    # Step 5: Build itinerary with meal locations
    itinerary_items = []
    current_time = start_time_minutes
    lunch_added = False
    item_id = 1
    
    # Track coordinates for mapping
    waypoint_coords = []
    
    for i, idx in enumerate(route_indices):
        loc_data = locations_data[idx]
        loc = locations[idx]
        
        # Calculate arrival time
        if i > 0:
            prev_idx = route_indices[i - 1]
            travel_time = travel_matrix[prev_idx][idx]
            current_time += travel_time
        
        # Wait for opening if necessary
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
                itinerary_items.append({
                    "id": str(item_id),
                    "name": lunch_restaurant["name"],
                    "time": format_time_12hr(current_time),
                    "duration": "1 hour",
                    "address": lunch_restaurant.get("address", ""),
                    "openingHours": f"{format_time_12hr(lunch_restaurant.get('open_time', 720))} - {format_time_12hr(lunch_restaurant.get('close_time', 1320))}",
                    "tags": ["Lunch"],
                    "websiteUrl": None,
                    "isMeal": "lunch",
                    "lat": lunch_restaurant["lat"],
                    "lon": lunch_restaurant["lon"]
                })
                waypoint_coords.append({
                    "lat": lunch_restaurant["lat"],
                    "lng": lunch_restaurant["lon"]
                })
                item_id += 1
                current_time += 60
                lunch_added = True
        
        # Add the location to itinerary
        if idx != hotel_index or i == 0:  # Add hotel only at start
            tags = []
            
            # Determine tags based on location type
            name_lower = loc.name.lower()
            if any(word in name_lower for word in ["museum", "gallery"]):
                tags.append("Cultural")
            elif any(word in name_lower for word in ["tower", "monument"]):
                tags.append("Landmark")
            elif any(word in name_lower for word in ["park", "garden"]):
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
            
            if idx != hotel_index:  # Don't add hotel to waypoints
                waypoint_coords.append({
                    "lat": loc_data["lat"],
                    "lng": loc_data["lon"]
                })
            
            item_id += 1
            current_time += loc.duration
    
    # Step 6: Add dinner at the end
    if include_dinner and len(route_indices) > 1:
        last_idx = route_indices[-1]
        last_loc_data = locations_data[last_idx]
        
        dinner_restaurant = await find_restaurant_near_location(
            last_loc_data["lat"], last_loc_data["lon"], radius_m=2000
        )
        
        if dinner_restaurant:
            # Aim for dinner around 7-8 PM
            if current_time < 1080:
                current_time = 1260  # 7:00 PM
            
            itinerary_items.append({
                "id": str(item_id),
                "name": dinner_restaurant["name"],
                "time": format_time_12hr(current_time),
                "duration": "2 hour",
                "address": dinner_restaurant.get("address", ""),
                "openingHours": f"{format_time_12hr(dinner_restaurant.get('open_time', 720))} - {format_time_12hr(dinner_restaurant.get('close_time', 1320))}",
                "tags": ["Dinner"],
                "websiteUrl": None,
                "isMeal": "dinner",
                "lat": dinner_restaurant["lat"],
                "lon": dinner_restaurant["lon"]
            })
            waypoint_coords.append({
                "lat": dinner_restaurant["lat"],
                "lng": dinner_restaurant["lon"]
            })
    
    # Step 7: Build final response
    hotel_data = locations_data[hotel_index]
    
    result = {
        "itinerary": itinerary_items,
        "images": [],  # Could be populated with image search API
        "videos": [],  # Could be populated with YouTube API
        "coordinates": {
            "origin": {
                "lat": hotel_data["lat"],
                "lng": hotel_data["lon"]
            },
            "destination": {
                "lat": hotel_data["lat"],
                "lng": hotel_data["lon"]
            },
            "waypoints": waypoint_coords
        },
        "summary": {
            "total_locations": len(itinerary_items),
            "start_time": format_time_12hr(start_time_minutes),
            "end_time": format_time_12hr(current_time),
            "duration": format_duration(current_time - start_time_minutes)
        }
    }
    
    return result


# Testing Function***
async def main():
    """Example usage of the itinerary generator with command-line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate a travel itinerary')
    parser.add_argument('locations', nargs='+', help='List of location names (first one is hotel)')
    parser.add_argument('--city', default='Paris, France', help='City name (default: Paris, France)')
    parser.add_argument('--start-time', type=int, default=540, help='Start time in minutes from midnight (default: 540 = 9:00 AM)')
    parser.add_argument('--hotel-index', type=int, default=0, help='Index of hotel in location list (default: 0)')
    
    args = parser.parse_args()
    
    print(f"Generating itinerary for {args.city}...")
    print(f"Locations: {', '.join(args.locations)}")
    print()
    
    itinerary = await generate_itinerary(
        args.locations,
        city=args.city,
        start_time_minutes=args.start_time,
        hotel_index=args.hotel_index
    )
    
    print("\n=== ITINERARY ===")
    for item in itinerary["itinerary"]:
        meal_tag = f" [{item['isMeal'].upper()}]" if item['isMeal'] else ""
        print(f"{item['id']}. {item['name']}{meal_tag}")
        print(f"   Time: {item['time']} ({item['duration']})")
        print(f"   Address: {item['address']}")
        print()
    
    print(f"\n=== SUMMARY ===")
    print(f"Total locations: {itinerary['summary']['total_locations']}")
    print(f"Start: {itinerary['summary']['start_time']}")
    print(f"End: {itinerary['summary']['end_time']}")
    print(f"Total duration: {itinerary['summary']['duration']}")


if __name__ == "__main__":
    asyncio.run(main())