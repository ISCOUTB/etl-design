var grpc = require('@grpc/grpc-js');
var services = require('./clients/formula_parser_grpc_pb');
var { parseFormulaHandler } = require('./handlers/formulaParserHandler');

function parseFormula(call, callback) {
    callback(null, parseFormulaHandler(call.request.getFormula()));
}

function getServer() {
    var server = new grpc.Server();
    server.addService(services.FormulaParserService, {
        parseFormula: parseFormula
    });
    return server;
}


if (require.main === module) {
    var routeServer = getServer();
    routeServer.bindAsync('localhost:50052', grpc.ServerCredentials.createInsecure(), () => { });
}
