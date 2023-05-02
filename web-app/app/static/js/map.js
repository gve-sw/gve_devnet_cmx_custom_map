// setTimeout(function () {
//     window.dispatchEvent(new Event('resize'));
// });

// var map = L.map('map').setView([51.505, -0.09], 13);
//
// L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
//     maxZoom: 19,
//     attribution: '© OpenStreetMap'
// }).addTo(map);
//
// var marker = L.marker([51.5, -0.09]).addTo(map);
// var circle = L.circle([51.508, -0.11], {
//     color: 'red',
//     fillColor: '#f03',
//     fillOpacity: 0.5,
//     radius: 500
// }).addTo(map);
// var polygon = L.polygon([
//     [51.509, -0.08],
//     [51.503, -0.06],
//     [51.51, -0.047]
// ]).addTo(map);
//
// marker.bindPopup("<b>3A-70-4D-E4-B6-34</b><br>Printer").openPopup();


var map = L.map('map', {
    crs: L.CRS.Simple,
    minZoom: -1
});

var bounds = [[0,0], [433,260]];
var image = L.imageOverlay('/static/img/domain_4_1658734382680.PNG', bounds).addTo(map);

map.fitBounds(bounds);

var sol = L.latLng([ 317.6232, 10.859113 ]);
L.marker(sol).addTo(map);
map.setView( [70, 120], 1);