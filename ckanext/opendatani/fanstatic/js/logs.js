(function(){
   $("#table-item").DataTable({
         "processing": true,
         "ajax": {
            "url":"http://localhost:5000/api/action/logs_list",
            "dataSrc": "result"
                },
         "columns":[
             {
                "data":"message",
                "title": "Message"
             }
         ]
   });
})()