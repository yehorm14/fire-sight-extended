import { Marker, Pane, Popup } from 'react-leaflet';
import { useEffect, useMemo, useState } from 'react';
import L from 'leaflet';
import { EVENTS_API_URL } from '../../config';

/** Only show “big” events (major crowd / demand signal). */
const MIN_ATTENDANCE = 1000;

const eventAlertIcon = L.divIcon({
  className: 'event-marker-icon-root',
  html: `
    <div class="event-marker-badge" aria-hidden="true">
      <span class="event-marker-excl">!</span>
    </div>
  `,
  iconSize: [36, 36],
  iconAnchor: [18, 18],
  popupAnchor: [0, -22]
});

// Illustrative sample events, used when no VITE_EVENTS_API_URL is configured.
// Dates are offsets from today so the demo always has upcoming events to show.
const localDateString = (daysFromToday) => {
  const d = new Date();
  d.setDate(d.getDate() + daysFromToday);
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
};

const SAMPLE_EVENTS = [
  { id: 'evt-1', name: 'Glasgow City Marathon Expo', location: 'SEC Glasgow', days: 21, estimatedAttendance: 11000, lat: 55.8591, lng: -4.2887 },
  { id: 'evt-2', name: 'Summer Riverside Festival', location: 'Glasgow Green', days: 120, estimatedAttendance: 18000, lat: 55.8517, lng: -4.2369 },
  { id: 'evt-3', name: 'Innovation and Tech Summit', location: 'Scottish Event Campus', days: 240, estimatedAttendance: 7000, lat: 55.8598, lng: -4.288 },
  { id: 'evt-4', name: 'Winter Market Launch', location: 'George Square', days: 400, estimatedAttendance: 9500, lat: 55.8612, lng: -4.2518 }
];

// Built when the component mounts, not at module load, so dates track the current day.
const buildFallbackEvents = () =>
  SAMPLE_EVENTS.map(({ days, ...event }) => ({ ...event, date: localDateString(days) }));

const bigEvents = (events) => events.filter((e) => e.estimatedAttendance > MIN_ATTENDANCE);

const TIMEFRAME_TO_MONTHS = {
  Current: 1,
  'In 6 months': 6,
  'In 1 year': 12,
  'In 1.5 years': 18
};

const addMonths = (date, months) => {
  const nextDate = new Date(date);
  nextDate.setMonth(nextDate.getMonth() + months);
  return nextDate;
};

const normalizeEvent = (event, idx) => {
  const lat = Number(event.lat ?? event.latitude ?? event.coordinates?.lat);
  const lng = Number(event.lng ?? event.longitude ?? event.coordinates?.lng);
  const date = event.date ?? event.eventDate ?? event.startDate;

  if (!Number.isFinite(lat) || !Number.isFinite(lng) || !date) {
    return null;
  }

  return {
    id: event.id ?? `event-${idx}`,
    name: event.name ?? event.title ?? 'Unnamed event',
    location: event.location ?? event.venue ?? 'Location pending',
    date,
    estimatedAttendance: Number(
      event.estimatedAttendance ?? event.attendance ?? event.expectedAttendance ?? 0
    ),
    lat,
    lng
  };
};

const EventLayer = ({ timeFrame }) => {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    let cancelled = false;

    const fetchEvents = async () => {
      if (!EVENTS_API_URL) {
        setEvents(bigEvents(buildFallbackEvents()));
        return;
      }
      try {
        const response = await fetch(EVENTS_API_URL);
        if (!response.ok) {
          throw new Error('Failed to fetch events');
        }

        const payload = await response.json();
        const rawEvents = Array.isArray(payload) ? payload : payload.events ?? [];
        const parsedEvents = bigEvents(
          rawEvents.map((event, idx) => normalizeEvent(event, idx)).filter(Boolean)
        );

        if (!cancelled) {
          setEvents(parsedEvents.length > 0 ? parsedEvents : bigEvents(buildFallbackEvents()));
        }
      } catch {
        if (!cancelled) {
          setEvents(bigEvents(buildFallbackEvents()));
        }
      }
    };

    fetchEvents();

    return () => {
      cancelled = true;
    };
  }, []);

  const filteredEvents = useMemo(() => {
    const months = TIMEFRAME_TO_MONTHS[timeFrame] ?? 1;
    const now = new Date();
    const endDate = addMonths(now, months);

    return events.filter((event) => {
      const eventDate = new Date(event.date);
      return eventDate >= now && eventDate <= endDate;
    });
  }, [events, timeFrame]);

  return (
    <Pane name="eventMarkersPane" style={{ zIndex: 550 }}>
      {filteredEvents.map((event) => (
        <Marker
          key={event.id}
          position={[event.lat, event.lng]}
          icon={eventAlertIcon}
          eventHandlers={{
            mouseover: (e) => {
              e.target.openPopup();
            },
            click: (e) => {
              e.target.openPopup();
            }
          }}
        >
          <Popup offset={[0, -8]} closeButton={false}>
            <div className="event-popup">
              <div className="event-popup-header">
                <h3>{event.name}</h3>
                <span className="event-risk-tag">Higher fire risk</span>
              </div>

              <div className="event-popup-grid">
                <p>
                  <span>Location</span>
                  <strong>{event.location}</strong>
                </p>
                <p>
                  <span>Date</span>
                  <strong>{new Date(event.date).toLocaleDateString()}</strong>
                </p>
                <p>
                  <span>Estimated Attendance</span>
                  <strong>{event.estimatedAttendance.toLocaleString()}</strong>
                </p>
              </div>

              <p className="event-popup-note">
                Event demand may increase fire risk for this area in the selected timeframe.
              </p>
            </div>
          </Popup>
        </Marker>
      ))}
    </Pane>
  );
};

export default EventLayer;
