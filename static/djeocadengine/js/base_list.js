const map = L.map('engine-map');

function onEachFeature(feature, layer) {
  if (feature.properties && feature.properties.popupContent) {
    layer.bindPopup(feature.properties.popupContent.content, {minWidth: 256});
  }
}

function setLineStyle(feature) {
  if (feature.properties.popupContent.linetype) {
    return {"color": feature.properties.popupContent.color, "weight": 3 };
  } else {
    return {"color": feature.properties.popupContent.color, "weight": 3, dashArray: "10, 10" };
  }
}

const base_map = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
  {
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  });

const layer_control = L.control.layers(null).addTo(map);
const marker_layer = L.layerGroup().addTo(map);

function getCollections() {
  // add eventually inactive base layers so they can be removed
  base_map.addTo(map);
  // sat_map.addTo(map);
  // remove all layers from layer control and from map
  map.eachLayer(function (layer) {
    layer_control.removeLayer(layer);
    map.removeLayer(layer);
  });
  marker_layer.clearLayers();
  // add base layers back to map and layer control
  base_map.addTo(map);
  // add layer groups
  collection = JSON.parse(document.getElementById("layer_data").textContent);
  if (collection !== null) {
    for (layer_name of collection) {
      window[layer_name] = L.layerGroup().addTo(map);
      layer_control.addOverlay(window[layer_name], layer_name);
    }
  }
  marker_layer.addTo(map)
  // add objects to layers
  collection = JSON.parse(document.getElementById("marker_data").textContent);
  for (marker of collection.features) {
    // let author = marker.properties.popupContent.layer
    L.geoJson(marker, {onEachFeature: onEachFeature}).addTo(marker_layer);
  }
  // fit bounds
  if (collection.features.length !== 0) {
    map.fitBounds(L.geoJson(collection).getBounds(), {padding: [30,30]});
  } else {
    let lc = JSON.parse(document.getElementById("leaflet_config").textContent);
    map.setView(lc.DEFAULT_CENTER, lc.DEFAULT_ZOOM)
  }
  collection = JSON.parse(document.getElementById("line_data").textContent);
  if (collection !== null) {
    for (line of collection.features) {
      let name = line.properties.popupContent.layer
      L.geoJson(line, {style: setLineStyle, onEachFeature: onEachFeature}).addTo(window[name]);
    }
  }
}

getCollections()

addEventListener("refreshCollections", function(evt){
  getCollections();
})

function openDrawing(path) {
  htmx.ajax('GET', path, '#nav-card')
}

function onMapClick(e) {
  var map_status = JSON.parse(document.getElementById("map_status").textContent);
  if (map_status.map_on_click) {
    var inputlat = document.getElementById("id_lat");
    var inputlong = document.getElementById("id_long");
    inputlat.setAttribute('value', e.latlng.lat);
    inputlong.setAttribute('value', e.latlng.lng);
    marker_layer.clearLayers();
    L.marker([e.latlng.lat, e.latlng.lng]).addTo(marker_layer)
  }
}

map.on('click', onMapClick);
