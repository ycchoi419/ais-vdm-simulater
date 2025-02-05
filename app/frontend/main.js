// import 'ol/ol.css';
import { toLonLat, fromLonLat } from 'ol/proj';
import { Map, View } from 'ol';
import TileLayer from 'ol/layer/Tile';
import OSM from 'ol/source/OSM';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import { Feature } from 'ol';
import { LineString } from 'ol/geom';
import { Stroke, Style} from 'ol/style';
import { getDistance } from 'ol/sphere';
import GeoJSON from 'ol/format/GeoJSON.js';


let shipNumber = 1;

const simulationReq = {};  
const lineFeatures = {};

// const map = new Map({
//     target: 'map',
//     layers: [
//         new TileLayer({
//             source: new OSM()
//         })
//     ],
//     view: new View({
//         center: fromLonLat([127.032535, 37.497689]),
//         zoom: 4
//     })
// });

// const vectorSource = new VectorSource({
//   features: new GeoJSON().readFeatures(geojsonObject),
// });
// // Vector layer for drawing arrows and circle
// // const vectorSource = new VectorSource();
// const vectorLayer = new VectorLayer({
//   source: vectorSource,
//   Style: new Style({
//     stroke: new Stroke({
//       color: [255,255,255,1],
//       width: 10
//     })
//   })
// });


const vectorSource = new VectorSource({
  url: '127.0.0.1:8000/map/countries.json',
  format: new GeoJSON()
});

const vectorLayer = new VectorLayer({
  source: vectorSource,
//   style: styleFunction,
});

const map = new Map({
  layers: [
    // new TileLayer({
    //   source: new OSM(),
    // }),
    vectorLayer,
  ],
  target: 'map',
  view: new View({
    center: [0, 0],
    zoom: 2,
  }),
});

// map.addLayer(vectorLayer);

let startPoint = null;
let endPoint = null;
let tempFeature = null;
let course = 0;
let speed = 0;

// Handle first click (set start point)
map.on('click', function (evt) {
  if (!startPoint) {
      startPoint = toLonLat(evt.coordinate);
      document.getElementById('coords-text').innerHTML = 
          `Start: Lat ${startPoint[1].toFixed(6)}, Lon ${startPoint[0].toFixed(6)}<br>Move mouse to draw`;
  } else {
    // Finalize the arrow
    map.on('pointermove', updateArrow);
    let line = new LineString([fromLonLat(startPoint), fromLonLat(endPoint)]);
    let line_feature = new Feature({ geometry: line });
    line_feature.setStyle(
      new Style({
        stroke: new Stroke({
          color: `rgb(${Math.floor(Math.random() * 256)}, ${Math.floor(Math.random() * 256)}, ${Math.floor(Math.random() * 256)})`,
          width: 5
        })
      }))
    lineFeatures[`test_ship${shipNumber}`] = line_feature;
    vectorSource.removeFeature(tempFeature);
    vectorSource.addFeature(line_feature);
    simulationReq[`test_ship${shipNumber}`] = {
      course: course.toFixed(2),
      distance: 2,
      lat: startPoint[1].toFixed(6),
      lon: startPoint[0].toFixed(6),
      mmsi: 123456780 + shipNumber,
      send_period: 2,
      speed,
      time: {
        create_time: 0,
        end_time: 10
      }
    }
    shipNumber += 1;
    tempFeature = null;
    startPoint = null;
    endPoint = null;
    speed = 0;
    course = 0;
  }
  renderShipList();  
});

function renderShipList() {
  const shipList = document.getElementById('ship-list');
  shipList.innerHTML = '';
  
  Object.entries(simulationReq).forEach(([key, value]) => {
    const shipDiv = document.createElement('div');
    shipDiv.id = `ship-${key}`;
    shipDiv.innerHTML = `
      <strong>${key}:</strong> 
      <button class="delete-btn" data-key="${key}">delete</button><br>
      mmsi: ${value.mmsi} <br>
      lat: ${value.lat} <br>
      lon: ${value.lon} <br>
      course: ${value.course} <br>
      speed: ${value.speed} <br>
      ========================= <br>
    `;
    shipList.appendChild(shipDiv);
  });
  
  document.querySelectorAll('.delete-btn').forEach(button => {
    button.addEventListener('click', (event) => {
      const key = event.target.getAttribute('data-key');
      vectorSource.removeFeature(lineFeatures[key]);
      delete lineFeatures[key];
      deleteShip(key);
    });
  });
}

function deleteShip(key) {
  delete simulationReq[key];
  renderShipList();
}

map.on('pointermove', updateArrow);

map.on('contextmenu', function (evt) {
  evt.preventDefault();
  startPoint = null;
  endPoint = null;
  speed = 0;
  course = 0;
  if (tempFeature) {
      vectorSource.removeFeature(tempFeature);
  }
  document.getElementById('coords-text').innerHTML = 'Click to set start point';
});

function updateArrow(evt) {
  if (!startPoint) return;
  
  endPoint = toLonLat(evt.coordinate);
  course = calculateBearing(startPoint, endPoint);
  speed = getDistance(startPoint, endPoint) / 1000 * 0.5399568;
  drawArrow(startPoint, endPoint);

  document.getElementById('coords-text').innerHTML = 
    `Start: Lat ${startPoint[1].toFixed(6)}, Lon ${startPoint[0].toFixed(6)}<br>
    Course: ${course.toFixed(2)}°<br>
    Speed: ${speed} kn`;
}

// Function to draw arrow dynamically
function drawArrow(start, end) {
  const line = new LineString([fromLonLat(start), fromLonLat(end)]);
  
  if (tempFeature) {
      vectorSource.removeFeature(tempFeature);
  }

  tempFeature = new Feature({ geometry: line, 
    });
  vectorSource.addFeature(tempFeature);
}

// Function to calculate bearing (course) in degrees
function calculateBearing(start, end) {
    const [lon1, lat1] = start.map(deg => deg * (Math.PI / 180));
    const [lon2, lat2] = end.map(deg => deg * (Math.PI / 180));

    const dLon = lon2 - lon1;
    const y = Math.sin(dLon) * Math.cos(lat2);
    const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);
    let bearing = Math.atan2(y, x) * (180 / Math.PI);

    return (bearing + 360) % 360; // Normalize to 0-359.99°
}

document.getElementById("startButton").addEventListener("click", function() {
  fetch("http://127.0.0.1:8000/start", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({ships: simulationReq}) // Modify body data as needed
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById("result").innerText = JSON.stringify(data.message, null, 2);
    })
    .catch(error => {
        document.getElementById("result").innerText = "Error fetching data";
        console.error("Error:", error);
    });
});

document.getElementById("stopButton").addEventListener("click", function() {
  fetch("http://127.0.0.1:8000/stop")
      .then(response => response.json())
      .then(data => {
          document.getElementById("result").innerText = JSON.stringify(data.message, null, 2);
      })
      .catch(error => {
          document.getElementById("result").innerText = "Error fetching data";
          console.error("Error:", error);
      });
});