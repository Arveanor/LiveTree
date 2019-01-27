
$(document).ready(function(){
    //connect to the socket server.
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');
    var leaves = [{}]; // leafId

    //receive details from server
    socket.on('newgeneration', function(msg) {
    	console.log("Received generate leaf command");
        var ftable = document.getElementById('ftable' + msg.factoryId);
        var row = ftable.insertRow(1);
        row.id = 'leafrow' + msg.leafId;
        var cell = row.insertCell(0);
        cell.innerHTML = "&lt;Leaf " + msg.leafId + " Value " + msg.leafValue + "&gt;";
    });

    socket.on('delete_leaf', function(msg) {
        console.log("Received delete leaf command");
        var ftable = document.getElementById('ftable' + msg.factoryId);
        ftable.deleteRow(1);
    });

    socket.on('delete_factory', function(msg) {
        console.log("Received delete factory command")
        var toDelete = document.getElementById('ftable' + msg.factoryId);
        if(toDelete) toDelete.parentNode.removeChild(toDelete);
    });

    socket.on('modify_factory', function(msg) {
        console.log("Received modify factory command");
        var toModify = document.getElementById('ftable' + msg.factoryId);
        toModify.rows[0].cells[0].innerHTML = msg.factoryName + " (" + msg.factoryLow + 
            ":" + msg.factoryHigh + ") | " + "<a href=\"/modify/" + msg.factoryName + "\">Modify</a>";
    });

    socket.on('create', function(msg) {
        var ftable = document.createElement("TABLE");
        ftable.id = "ftable" + msg.factoryId;        
        var container = document.getElementById('maincontainer');

        var mainRow = ftable.insertRow(0);
        var mainCell = mainRow.insertCell(0);
        mainCell.innerHTML = msg.factoryName + " (1:15) | " + "<a href=\"/modify/" + msg.factoryName + "\">Modify</a>";
        mainCell.width = "160px";

        var generateCell = mainRow.insertCell(1);
        var genForm = document.createElement("form");
        var genName = document.createElement("input");
        var genCsrf = document.createElement("input");
        var genDiv = document.createElement("div");
        var genInput = document.createElement("input");
        var genLabel = document.createElement("label");
        var genButton = document.createElement("input");
        genForm.setAttribute('method', "post");
        genForm.setAttribute('action', "");
        genForm.setAttribute('class', "form");
        genForm.setAttribute('role', "form");
        genName.setAttribute('id', "factoryId");
        genName.setAttribute('name', "factoryId");
        genName.setAttribute('type', "hidden");
        genName.setAttribute('value', msg.factoryId);
        genCsrf.setAttribute('id', "csrf_token");
        genCsrf.setAttribute('name', "csrf_token");
        genCsrf.setAttribute('type', "hidden");
        genCsrf.setAttribute('value', msg.csrf_token);
        genDiv.setAttribute('class', "form-group requried");
        genInput.setAttribute('id', "numLeaves");
        genInput.setAttribute('class', "form-control");
        genInput.setAttribute('name', "numLeaves");
        genInput.setAttribute('required', "");
        genInput.setAttribute('type', "text");
        genInput.setAttribute('value', "");
        genLabel.setAttribute('class', "control-label");
        genLabel.setAttribute('for', "numLeaves");
        genLabel.innerHTML = "Number of Leaves";
        genButton.setAttribute('id', "generate");
        genButton.setAttribute('class', "btn btn-default");
        genButton.setAttribute('name', "generate");
        genButton.setAttribute('type', "submit");
        genButton.setAttribute('value', "Generate");

        genDiv.appendChild(genLabel);
        genDiv.appendChild(genInput);
        genForm.appendChild(genName);
        genForm.appendChild(genCsrf);
        genForm.appendChild(genDiv);
        genForm.appendChild(genButton);
        generateCell.appendChild(genForm);

        var deleteCell = mainRow.insertCell(2);
        var delForm = document.createElement("form");
        var delName = document.createElement("input");
        var delCsrf = document.createElement("input");
        var delButton = document.createElement("input");

        delForm.setAttribute('method', "post");
        delForm.setAttribute('action', "");
        delForm.setAttribute('class', "form");
        delForm.setAttribute('role', "form");
        delName.setAttribute('id', "factoryId");
        delName.setAttribute('name', "factoryId");
        delName.setAttribute('type', "hidden");
        delName.setAttribute('value', msg.factoryId);
        delCsrf.setAttribute('id', "csrf_token");
        delCsrf.setAttribute('name', "csrf_token");
        delCsrf.setAttribute('type', "hidden");
        delCsrf.setAttribute('value', msg.csrf_token);
        delButton.setAttribute('id', "delete");
        delButton.setAttribute('class', "btn btn-default");
        delButton.setAttribute('name', "delete");
        delButton.setAttribute('type', "submit");
        delButton.setAttribute('value', "Delete");

        delForm.appendChild(delName);
        delForm.appendChild(delCsrf);
        delForm.appendChild(delButton);
        deleteCell.appendChild(delForm);

        container.appendChild(ftable);
        console.log("received create command");
        console.log(msg.factoryId + " " + msg.csrf_token);
    });

});