var minEsc = 1100;
var maxVal = 2000;
var waitTime = 2.0;
var samplesAvg = 5;
var repeat = 1.0;
var throttleIncrement = 50;
var filePrefix = "xNova-TM";

function readSensor(){
    rcb.console.setVerbose(false);
    rcb.sensors.read(readDone, samplesAvg);
    rcb.console.setVerbose(true);
}

function readDone(result){
    rcb.console.setVerbose(false);
    rcb.files.newLogEntry(result, readSensor);
    rcb.console.setVerbose(true);
}

function performRampStep(min_value, max_value, maxLimit, increment) {
    if (max_value > maxLimit) {
        rcb.console.print("Script done. Closing down...");
        return;
    }

    rcb.console.print("Up from " + min_value + " to " + max_value);
    rcb.output.ramp("esc", min_value, max_value, waitTime, function () {
        rcb.console.print("Plateau at max...");
        rcb.wait(function () {
            min_value = max_value;
            performRampStep(min_value, min_value + increment, maxLimit, increment);
        }, waitTime);
    });
}

function runScript() {
    rcb.output.set("esc", minEsc);
    var min_value = 1100;
    var maxLimit = 1600;
    var increment = throttleIncrement;

    performRampStep(min_value, min_value + increment, maxLimit, increment);
}

// Inicio de la ejecución
rcb.files.newLogFile({prefix: filePrefix});
readSensor();

rcb.console.print("Initializing ESC...");
rcb.output.set("esc", 1000);

rcb.wait(runScript, 3);