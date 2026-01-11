# FIX API - Flask Endpoint Integration Points

This document lists all locations in the frontend code where Flask API endpoints need to be called.

## Files with FIX API Comments

### 1. **frontend/src/components/TripForm.tsx**
- **Location**: `handlePlanTrip()` function (line ~57-67)
- **What**: Form submission when user clicks "Create My Adventure"
- **API Needed**: `POST /api/generate-itinerary`
- **Input**: User trip data (location, vibes, days, budget)
- **Expected Output**: Initial itinerary data or just confirmation to proceed
- **Action**: Call Flask endpoint with trip parameters and store response in sessionStorage

---

### 2. **frontend/src/pages/Loading.tsx**
- **Location**: Multiple places (lines ~34-66)
- **What**: Monitor itinerary generation progress and phase transitions
- **API Needed**: 
  - `GET /api/generate-itinerary-status` (optional - to track progress)
  - `GET /api/itinerary-results` (to fetch final results)
- **Input**: Trip ID or location from sessionStorage
- **Expected Output**: Current phase status, progress, and final results
- **Action**: 
  1. Replace hardcoded timers with actual API polling
  2. Store API results in sessionStorage before navigating to results page
  3. Retrieve venue data from API instead of mockVenues

---

### 3. **frontend/src/pages/Results.tsx**
- **Location**: Multiple mock data objects (lines ~11-110)
- **What**: Display itinerary, images, videos, and map coordinates
- **API Data to Replace**:
  1. `mockItinerary` - Array of activities with time, duration, address, hours, tags, website
  2. `mockImages` - Array of image objects with url and caption
  3. `mockVideos` - Array of video objects with youtubeId and title
  4. `mockCoordinates` - Route coordinates with origin, destination, waypoints
- **API Needed**: Already called from Loading.tsx, data should be in sessionStorage
- **Action**: Fetch itinerary results from sessionStorage that were populated by Loading.tsx

---

### 4. **frontend/src/components/ItineraryCard.tsx**
- **Location**: Reserve button onClick handler (line ~131-139)
- **What**: Handle reservation/booking action when user clicks Reserve button
- **API Needed**: `POST /api/reserve` or `POST /api/book`
- **Input**: Item details (name, time, address, websiteUrl, etc.)
- **Expected Output**: Confirmation of reservation or redirect to booking page
- **Action**: Replace the window.open() call with API integration to handle reservation

---

## API Endpoint Specifications (To Be Implemented in Flask)

### 1. POST /api/generate-itinerary
**Request:**
```json
{
  "location": "San Diego, California",
  "vibes": ["chill", "romantic"],
  "days": 3,
  "budget": 2000
}
```

**Response:**
```json
{
  "itinerary": [...],
  "venues": [...],
  "images": [...],
  "videos": [...],
  "coordinates": {...}
}
```

### 2. GET /api/generate-itinerary-status (Optional)
**Query Parameters**: tripId, location

**Response:**
```json
{
  "phase": "searching|shortlisting|complete",
  "progress": 0-100
}
```

### 3. GET /api/itinerary-results
**Query Parameters**: location, tripId

**Response**: Same as POST /api/generate-itinerary

### 4. POST /api/reserve
**Request:**
```json
{
  "itemId": "1",
  "name": "Sunrise at Sunset Cliffs",
  "time": "8:00 AM",
  "websiteUrl": "..."
}
```

**Response:**
```json
{
  "success": true,
  "confirmationId": "ABC123",
  "bookingUrl": "..."
}
```

---

## Implementation Priority

1. **HIGH** - TripForm.tsx `handlePlanTrip()` - This is the entry point
2. **HIGH** - Loading.tsx phase transitions and result fetching - Core experience
3. **HIGH** - Results.tsx data loading - Display of results
4. **MEDIUM** - ItineraryCard.tsx Reserve button - Booking functionality
5. **LOW** - LocationSearch.tsx (currently uses OpenStreetMap) - Optional to integrate with Flask

---

## Notes

- All API calls should handle errors gracefully with proper error messages to user
- Consider adding loading states and skeleton screens where needed
- Implement proper error boundaries and retry logic
- Store results in sessionStorage to persist data across page navigations
- Consider implementing request cancellation for cleanup on unmount
