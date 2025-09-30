// 🌍 WorldWind setup
const wwd = new WorldWind.WorldWindow("canvasOne");
wwd.addLayer(new WorldWind.BMNGOneImageLayer());
wwd.addLayer(new WorldWind.BMNGLandsatLayer());
wwd.addLayer(new WorldWind.AtmosphereLayer());
wwd.addLayer(new WorldWind.CompassLayer());
wwd.addLayer(new WorldWind.CoordinatesDisplayLayer(wwd));
wwd.addLayer(new WorldWind.ViewControlsLayer(wwd));

// Start at Cairo
wwd.goTo(new WorldWind.Position(30.0444, 31.2357, 1000000));

const placemarkLayer = new WorldWind.RenderableLayer("Markers");
wwd.addLayer(placemarkLayer);

function addMarker(lat, lon) {
  placemarkLayer.removeAllRenderables();

  const attrs = new WorldWind.PlacemarkAttributes(null);
  attrs.imageSource = "https://upload.wikimedia.org/wikipedia/commons/e/ec/RedDot.svg";
  attrs.imageScale = 0.25;

  const pos = new WorldWind.Position(lat, lon, 1);
  const placemark = new WorldWind.Placemark(pos, false, attrs);

  placemarkLayer.addRenderable(placemark);
}

// 🔑 OpenCage API key
const apiKey = "953b73b1da854a14aa917ece77d7bc97";

// Google Maps reference
let map;
let googleMarker;

// Initialize Google Map
function initMap() {
  map = new google.maps.Map(document.getElementById("map"), {
    center: { lat: 30.0444, lng: 31.2357 },
    zoom: 5,
  });

  googleMarker = new google.maps.Marker({
    map: map,
    draggable: true,
  });

  // Capture click on Google Map
  map.addListener("click", (event) => {
    const lat = event.latLng.lat();
    const lng = event.latLng.lng();
    setMarker(lat, lng);
    sendToBackend(lat, lng);
  });

  // Capture drag end on marker
  googleMarker.addListener("dragend", (event) => {
    const lat = event.latLng.lat();
    const lng = event.latLng.lng();
    sendToBackend(lat, lng);
  });
}

// Place marker on Google Map
function setMarker(lat, lng) {
  googleMarker.setPosition({ lat, lng });
  map.setCenter({ lat, lng });
  map.setZoom(10);
}

// Function to search location via OpenCage
function searchLocation() {
  const location = document.getElementById("locationInput").value.trim();
  if (!location) return alert("Please enter a city or country.");

  const url = `https://api.opencagedata.com/geocode/v1/json?q=${encodeURIComponent(location)}&key=${apiKey}&no_annotations=1`;

  fetch(url)
    .then(res => res.json())
    .then(data => {
      if (data.results && data.results.length > 0) {
        const { lat, lng } = data.results[0].geometry;

        // Move WorldWind camera + marker
        wwd.goTo(new WorldWind.Position(lat, lng, 1000000));
        addMarker(lat, lng);

        // Move Google Map marker
        setMarker(lat, lng);
        sendToBackend(lat, lng);
      } else {
        alert("Location not found.");
      }
    })
    .catch(err => {
      console.error("Error:", err);
      alert("An error occurred while searching.");
    });
}

// Example: send picked coordinates to backend
function sendToBackend(lat, lng) {
  console.log("Sending coordinates:", lat, lng);

  // Example POST request
  /*
  fetch("/save-coordinates", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lat, lng })
  })
  .then(res => res.json())
  .then(data => console.log("Backend response:", data));
  */
}
