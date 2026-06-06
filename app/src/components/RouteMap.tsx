import { useEffect, useRef } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

mapboxgl.accessToken =
  "pk.eyJ1IjoibGVvbmFyZG8wNDA2IiwiYSI6ImNtbnhqamdraDAzNWUyeW9sNnN0OXdlM3QifQ.7VbegBLq_o6xLiIoMni9nQ";

const ROUTE: [number, number][] = [
  [-99.1556, 19.4015],
  [-99.1492, 19.4078],
  [-99.1430, 19.4142],
  [-99.1368, 19.4205],
  [-99.1310, 19.4268],
  [-99.1245, 19.4326],
];

export function RouteMap() {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: "mapbox://styles/mapbox/dark-v11",
      center: [-99.1332, 19.4326],
      zoom: 12,
      attributionControl: false,
      interactive: true,
    });
    mapRef.current = map;

    map.on("load", () => {
      map.addSource("route", {
        type: "geojson",
        data: {
          type: "Feature",
          properties: {},
          geometry: { type: "LineString", coordinates: ROUTE },
        },
      });
      map.addLayer({
        id: "route-glow",
        type: "line",
        source: "route",
        layout: { "line-join": "round", "line-cap": "round" },
        paint: {
          "line-color": "#2DD4BF",
          "line-width": 8,
          "line-opacity": 0.25,
          "line-blur": 4,
        },
      });
      map.addLayer({
        id: "route-line",
        type: "line",
        source: "route",
        layout: { "line-join": "round", "line-cap": "round" },
        paint: { "line-color": "#2DD4BF", "line-width": 3 },
      });

      const start = document.createElement("div");
      start.style.cssText =
        "width:14px;height:14px;border-radius:9999px;background:#2DD4BF;border:2px solid #0F172A;box-shadow:0 0 0 3px rgba(45,212,191,0.35);";
      new mapboxgl.Marker(start).setLngLat(ROUTE[0]).addTo(map);

      const end = document.createElement("div");
      end.style.cssText =
        "width:14px;height:14px;border-radius:9999px;background:#fff;border:2px solid #2DD4BF;box-shadow:0 0 0 3px rgba(45,212,191,0.35);";
      new mapboxgl.Marker(end).setLngLat(ROUTE[ROUTE.length - 1]).addTo(map);
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="h-40 w-full overflow-hidden rounded-xl border border-slate-700/60"
    />
  );
}
