const API_URL = 'https://your-api-url.com/api/covid'; // Replace this

function interpolateColor(color1, color2, factor) {
  return color1.map((c, i) => Math.round(c + factor * (color2[i] - c)));
}

function rgbToHex(rgb) {
  return "#" + rgb.map(x => x.toString(16).padStart(2, '0')).join('');
}

const white = [255, 255, 255];
const lightRed = [255, 102, 102];
const darkRed = [128, 0, 0];

function getColor(value, min, max) {
  if (value <= min) return rgbToHex(white);
  if (value >= max) return rgbToHex(darkRed);

  const mid = min + (max - min) / 2;
  if (value < mid) {
    const factor = (value - min) / (mid - min);
    return rgbToHex(interpolateColor(white, lightRed, factor));
  } else {
    const factor = (value - mid) / (max - mid);
    return rgbToHex(interpolateColor(lightRed, darkRed, factor));
  }
}

const map = L.map('map').setView([23.5937, 80.9629], 5);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 10,
  attribution: '© OpenStreetMap'
}).addTo(map);

fetch(API_URL)
  .then(res => res.json())
  .then(covidData => {
    const activeCases = covidData.map(s => s.active);
    const min = Math.min(...activeCases);
    const max = Math.max(...activeCases);

    fetch('india_states.geojson')
      .then(res => res.json())
      .then(geojson => {
        L.geoJSON(geojson, {
          style: function (feature) {
            const stateName = feature.properties.STNAME_SH.trim().toLowerCase();
            const stateData = covidData.find(s => s.state.toLowerCase() === stateName);
            const active = stateData ? stateData.active : 0;
            return {
              fillColor: getColor(active, min, max),
              weight: 1,
              color: '#aaa',
              fillOpacity: 0.7
            };
          },
          onEachFeature: function (feature, layer) {
            const stateName = feature.properties.STNAME_SH.trim();
            const stateData = covidData.find(s => s.state.toLowerCase() === stateName.toLowerCase());
            const active = stateData ? stateData.active : 'N/A';
            layer.bindTooltip(`<strong>${stateName}</strong><br/>Active Cases: ${active}`, { sticky: true });
          }
        }).addTo(map);
      })
      .catch(err => console.error("GeoJSON load error:", err));
  })
  .catch(err => console.error("COVID data fetch error:", err));
