console.log('hello');
var http = require('http');
var pdfToJSON = require('./ ');

//To be edited
http.createServer(function (req, res) {
  res.writeHead(200, {'Content-Type': 'text/html'});
  res.write("The date and time are currently: " + dt.myDateTime());
  res.end();
}).listen(8080);