var lastLog;
console.rawLog = console.log;
console.log = function(s) {
	console.rawLog(s);
	lastLog = s;
}

const output = document.getElementById("output");

const editor = CodeMirror.fromTextArea(document.getElementById("code"), {
    mode: {
        name: "python",
        version: 3,
        singleLineStringErrors: false
    },
    theme: "blackboard",
    lineNumbers: true,
    indentUnit: 4,
    matchBrackets: true,
    lineWrapping: true,
    spellcheck: true
});

editor.setValue(`# This is a sample Python script.

def main():
    return "Hello World!"

main()`);

output.value = "Initializing...\n";

async function main() {
    let pyodide = await loadPyodide({ indexURL: "https://cdn.jsdelivr.net/pyodide/v0.21.0/full/" });
    output.value += "Ready!\n";
    return pyodide
}

let pyodideReadyPromise = main();

function addToOutput(s) {
    output.value += ">>>" + s + "\n";
}

function clearHistory() {
      output.value = "";
}

async function evaluatePython() {
    let pyodide = await pyodideReadyPromise;
    try {
        await pyodide.loadPackagesFromImports(editor.getValue());
        let output = await pyodide.runPython(editor.getValue());
        if (output == undefined){
            output = lastLog;
        }
        addToOutput(output);
    } catch (err) {
        addToOutput(err);
    }
}

async function chat() {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "http://0.0.0.0:8000/codeLlama");
    var prompt = document.getElementById("prompt").value;
    var promptInput = document.getElementById("prompt-input").value;
    if (prompt == ''){
        alert("Instruction cannot be empty!");
    }else{
        let data = {"prompt": prompt, "input": promptInput};
        xhr.send(JSON.stringify(data));
        document.getElementById("cursor-btn").setAttribute("style", "animation:spin 2s linear infinite;");
        xhr.onreadystatechange = function() {
            if(xhr.readyState == 4 && xhr.status == 200 ){
                document.getElementById("cursor-btn").setAttribute("style", "animation:None;");
                let responseText = JSON.parse(xhr.responseText);
                editor.setValue(responseText.data.response);
            }
        }
    }
}