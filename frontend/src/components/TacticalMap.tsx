import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

interface IntelligenceAlert {
  actor_1: string | null;
  location_text: string | null;
  severity_score: number;
}

interface TacticalMapProps {
  alerts: IntelligenceAlert[];
}

// Quick-access coordinates for the current conflict zone to ensure instant plotting
const GEOCACHE: { [key: string]: [number, number] } = {
  "Tehran": [35.6892, 51.3890],
  "Bushehr": [28.9234, 50.8203],
  "Abu Dhabi": [24.4539, 54.3773],
  "Tyre": [33.2708, 35.1962],
  "Karaj": [35.8355, 50.9915],
  "Strait of Hormuz": [26.5667, 56.2500],
  "Damascus": [33.5138, 36.2765],
  "Riyadh": [24.7136, 46.6753],
  "Kuwait": [29.3759, 47.9774],
  "Basra": [30.5081, 47.7835],
};

const TacticalMap = ({ alerts }: TacticalMapProps) => {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<L.Map | null>(null);
  const markersLayer = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!mapRef.current || mapInstance.current) return;

    // Initialize Map
    const map = L.map(mapRef.current, {
      center: [30, 45], // Centered on Middle East/Gulf region
      zoom: 4,
      zoomControl: false,
      attributionControl: false,
    });

    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png").addTo(map);
    
    mapInstance.current = map;
    markersLayer.current = L.layerGroup().addTo(map);

    return () => {
      map.remove();
      mapInstance.current = null;
    };
  }, []);

  useEffect(() => {
    if (!markersLayer.current || !alerts) return;

    // Clear old markers before redrawing
    markersLayer.current.clearLayers();

    alerts.forEach((alert) => {
      const location = alert.location_text || "";
      // Search for the location in our cache (case-insensitive)
      const cachedKey = Object.keys(GEOCACHE).find(key => 
        location.toLowerCase().includes(key.toLowerCase())
      );
      
      const coords = cachedKey ? GEOCACHE[cachedKey] : null;

      if (coords) {
        const color = alert.severity_score >= 0.7 ? "#FF3333" : "#33FF33";
        
        const pulseIcon = L.divIcon({
          className: "custom-pulse",
          html: `
            <div style="position:relative;width:20px;height:20px;">
              <div style="position:absolute;width:12px;height:12px;background:${color};border-radius:50%;top:4px;left:4px;box-shadow:0 0 10px ${color};"></div>
              <div class="radar-pulse" style="position:absolute;width:12px;height:12px;border:2px solid ${color};border-radius:50%;top:4px;left:4px;animation: pulse 2s infinite;"></div>
            </div>
          `,
          iconSize: [20, 20],
          iconAnchor: [10, 10],
        });

        L.marker(coords, { icon: pulseIcon })
          .addTo(markersLayer.current!)
          .bindTooltip(`${alert.actor_1}: ${alert.location_text}`, {
            className: "bg-background text-foreground border-border font-mono text-xs",
          });
      }
    });
  }, [alerts]);

  return <div ref={mapRef} className="w-full h-[400px] border border-border border-glow rounded-none" />;
};

export default TacticalMap;