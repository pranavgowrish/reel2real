INF = float("inf")

class Location:
    def __init__(self, name, open_time, close_time, duration, priority=None):
        """
        Location with time windows and duration.
        Priority is deprecated - algorithm now optimizes purely on travel time + waiting time.
        """
        self.name = name
        self.open = open_time
        self.close = close_time
        self.duration = duration
        self.priority = priority  # Kept for backward compatibility, but not used in cost calculation


def build_itinerary(locations, travel_time, start_idx, start_time, return_to_hotel=True, lunch_window=(720, 900), lunch_duration=60, restaurant_locations=None):
    """
    Build itinerary with hotel return and automatic lunch break.
    
    Args:
        locations: List of Location objects
        travel_time: Travel time matrix
        start_idx: Starting location index (hotel)
        start_time: Starting time in minutes
        return_to_hotel: Whether to return to hotel at end
        lunch_window: (start_min, end_min) lunch time window (default 12-3 PM = 720-900)
        lunch_duration: Duration of lunch break in minutes (default 60)
        restaurant_locations: List of indices that are restaurants (optional, auto-detected if None)
    
    Returns:
        route: List of location indices
        current_time: End time
        meal_times: Dict with lunch_time and dinner_time (if applicable)
    """
    n = len(locations)
    visited = [False] * n
    # Hotel is starting point, don't mark as visited so we can return
    
    route = [start_idx]
    current = start_idx
    current_time = start_time
    lunch_taken = False
    meal_times = {}
    
    # Auto-detect restaurants if not provided
    if restaurant_locations is None:
        restaurant_locations = []
        for i in range(n):
            if i == start_idx:
                continue
            name_lower = locations[i].name.lower()
            is_restaurant = (
                "restaurant" in name_lower or
                "cafe" in name_lower or
                "café" in name_lower or
                "bistro" in name_lower or
                "eatery" in name_lower or
                "food" in name_lower or
                "dining" in name_lower
            )
            if is_restaurant:
                restaurant_locations.append(i)

    while True:
        # Check if we need lunch (between 12-3 PM window)
        lunch_start, lunch_end = lunch_window
        # Try to take lunch if we're in the window and haven't had it yet
        if not lunch_taken and current_time <= lunch_end:
            should_take_lunch = False
            
            # If we're already past lunch start, take lunch now
            if current_time >= lunch_start:
                should_take_lunch = True
            # If we'll arrive at next location after lunch window, take lunch first
            elif current_time < lunch_start:
                # Estimate if next location would push us past lunch window
                # We'll take lunch if we're close to lunch time (within 30 min)
                if lunch_start - current_time <= 30:
                    should_take_lunch = True
            
            if should_take_lunch:
                # Time for lunch - find nearest restaurant
                best_restaurant = None
                best_restaurant_cost = INF
                
                # Try restaurant locations first (from the list of known restaurants)
                for i in restaurant_locations:
                    if visited[i] or i == start_idx:
                        continue
                        
                    travel = travel_time[current][i]
                    arrival = current_time + travel
                    
                    # Restaurant should be open and we should arrive before lunch window ends
                    if arrival < locations[i].open:
                        arrival = locations[i].open
                    if arrival > locations[i].close or arrival > lunch_end:
                        continue
                    
                    # Cost is travel time (prefer closer restaurants)
                    cost = travel
                    if cost < best_restaurant_cost:
                        best_restaurant_cost = cost
                        best_restaurant = i
                
                # If no restaurant found in list, check all unvisited locations
                if best_restaurant is None:
                    for i in range(n):
                        if visited[i] or i == start_idx:
                            continue
                        
                        # Check if location can serve as lunch spot (open during lunch)
                        travel = travel_time[current][i]
                        arrival = current_time + travel
                        
                        if arrival < locations[i].open:
                            arrival = locations[i].open
                        if arrival > lunch_end:
                            continue
                        
                        # Must arrive within lunch window
                        if arrival < lunch_start:
                            arrival = lunch_start  # Wait until lunch time
                        
                        if arrival <= lunch_end:
                            # Prefer locations with shorter duration (quick lunch spots)
                            cost = travel + max(0, arrival - current_time) + locations[i].duration
                            if cost < best_restaurant_cost:
                                best_restaurant_cost = cost
                                best_restaurant = i
                
                if best_restaurant is not None:
                    # Go to restaurant for lunch
                    travel = travel_time[current][best_restaurant]
                    arrival = current_time + travel
                    
                    if arrival < locations[best_restaurant].open:
                        arrival = locations[best_restaurant].open
                    if arrival < lunch_start:
                        arrival = lunch_start  # Wait until lunch window starts
                    
                    route.append(best_restaurant)
                    meal_times['lunch_time'] = arrival
                    meal_times['lunch_location'] = best_restaurant
                    current_time = arrival + lunch_duration
                    visited[best_restaurant] = True
                    current = best_restaurant
                    lunch_taken = True
                    continue
                else:
                    # No restaurant found, skip lunch and continue
                    lunch_taken = True  # Mark as taken to avoid trying again
        
        # Normal location selection
        best_next = None
        best_cost = INF

        for i in range(n):
            if visited[i] or i == start_idx:  # Skip hotel and visited locations
                continue

            travel = travel_time[current][i]
            arrival = current_time + travel

            if arrival < locations[i].open:
                arrival = locations[i].open

            if arrival > locations[i].close:
                continue

            waiting = max(0, locations[i].open - (current_time + travel))

            # Cost is purely based on travel time + waiting time (TSP-like with time windows)
            # No priority penalty - optimize purely on time efficiency
            cost = travel + waiting

            if cost < best_cost:
                best_cost = cost
                best_next = i

        if best_next is None:
            break

        travel = travel_time[current][best_next]
        arrival = current_time + travel

        if arrival < locations[best_next].open:
            arrival = locations[best_next].open

        current_time = arrival + locations[best_next].duration
        visited[best_next] = True
        current = best_next
        route.append(best_next)

    # Return to hotel at end of day
    if return_to_hotel and current != start_idx:
        travel = travel_time[current][start_idx]
        arrival = current_time + travel
        current_time = arrival  # Arrive at hotel for dinner
        route.append(start_idx)
        meal_times['dinner_time'] = current_time
        meal_times['dinner_location'] = start_idx
    
    return route, current_time, meal_times


def main():
    n = int(input())
    locations = []

    for _ in range(n):
        parts = input().split()
        name = parts[0]
        open_t = int(parts[1])
        close_t = int(parts[2])
        duration = int(parts[3])
        priority = int(parts[4]) if len(parts) > 4 else None  # Optional for backward compatibility
        locations.append(
            Location(
                name,
                open_t,
                close_t,
                duration,
                priority
            )
        )

    travel_time = []
    for _ in range(n):
        travel_time.append(list(map(int, input().split())))

    start_idx, start_time = map(int, input().split())

    route, end_time = build_itinerary(
        locations, travel_time, start_idx, start_time
    )

    print("\nFinal Itinerary:")
    for idx in route:
        print(f"- {locations[idx].name}")

    print(f"\nFinished at minute: {end_time}")


if __name__ == "__main__":
    main()
