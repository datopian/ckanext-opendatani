(function() {
    $("#table-item").DataTable({
        "processing": true,
        "language": {
            "emptyTable": "No data available from the SFTP logs"
        },
        "ajax": {
            "url": "http://localhost:5000/api/action/logs_list",
            "dataSrc": "result"
        },
        "columns": [{
            "data": "message",
            "title": "Message"
        },{
            "data": "created",
            "title": "Time"
        },]
    });
})()