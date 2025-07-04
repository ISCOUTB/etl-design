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
    const host = process.env.FORMULA_PARSER_HOST || 'localhost';
    const port = process.env.FORMULA_PARSER_PORT || '50052';
    console.log(`Starting Formula Parser Server on ${host}:${port}`);
    routeServer.bindAsync(`${host}:${port}`, grpc.ServerCredentials.createInsecure(), () => { });
}
