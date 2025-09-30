// Create WorldWindow linked to our canvas
const wwd = new WorldWind.WorldWindow("canvasOne");

// 🌍 Base Earth layers
wwd.addLayer(new WorldWind.BMNGOneImageLayer());   // Blue Marble
wwd.addLayer(new WorldWind.BMNGLandsatLayer());    // Satellite overlay
wwd.addLayer(new WorldWind.AtmosphereLayer());     // Clouds & atmosphere

// 🧭 UI helpers
wwd.addLayer(new WorldWind.CompassLayer());
wwd.addLayer(new WorldWind.CoordinatesDisplayLayer(wwd));
wwd.addLayer(new WorldWind.ViewControlsLayer(wwd));

// Initial camera position: Cairo
wwd.goTo(new WorldWind.Position(30.0444, 31.2357, 1000000));

// Create placemark layer once
const placemarkLayer = new WorldWind.RenderableLayer("Search Markers");
wwd.addLayer(placemarkLayer);

// Function to add red dot placemark
function addMarker(lat, lon) {
  placemarkLayer.removeAllRenderables();

  const placemarkAttributes = new WorldWind.PlacemarkAttributes(null);
  placemarkAttributes.imageSource = "https://upload.wikimedia.org/wikipedia/commons/e/ec/RedDot.svg";
  placemarkAttributes.imageScale = 0.25;

  const placemarkPosition = new WorldWind.Position(lat, lon, 1);
  const placemark = new WorldWind.Placemark(placemarkPosition, false, placemarkAttributes);

  placemarkLayer.addRenderable(placemark);
}

// Replace with your own OpenCage API key
const apiKey = "953b73b1da854a14aa917ece77d7bc97";

// Function to search city and fly to it
function searchLocation() {
  const location = document.getElementById("locationInput").value.trim();

  if (!location) return alert("Please enter a city or location.");

  const url = `https://api.opencagedata.com/geocode/v1/json?q=${encodeURIComponent(location)}&key=${apiKey}&no_annotations=1`;

  fetch(url)
    .then(res => res.json())
    .then(data => {
      if (data.results && data.results.length > 0) {
        const { lat, lng } = data.results[0].geometry;

        // Fly to location on WorldWind
        wwd.goTo(new WorldWind.Position(lat, lng, 1000000));
        addMarker(lat, lng);

        // ✅ Redirect to Google Maps with chosen location
        setTimeout(() => {
          const mapsUrl = `https://www.google.com/maps?q=${lat},${lng}`;
          window.open(mapsUrl, "_blank"); // opens in new tab
        }, 2000); // wait 2 seconds so user sees animation before redirect
      } else {
        alert("Location not found.");
      }
    })
    .catch(err => {
      console.error("Error:", err);
      alert("An error occurred while searching.");
    });
}
