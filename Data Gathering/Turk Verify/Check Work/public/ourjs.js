$(document).ready(function() {
    var subphrase = $("#subphrases").text().replace(/\s+/g, '').split("");
    var tweet = $("#tweet").text().trim().split(" ");
    var id = $("#row_id").text().trim();
    printAnnotatedTweet(tweet, subphrase);

    $(document).bind('keypress', function(e) {
        var code = e.keyCode || e.which;
        // A For Accept
        if(code == 97) {
            window.location.href = 'next?id='+id+'&accept=true';
        }
        // R for Reject
        if(code == 114) {
            var retVal = prompt("Enter reason : ", "");
            console.log(retVal)
            window.location.href = 'next?id='+id+'&accept=false'+'&feedback='+encodeURIComponent(retVal);
        }
        // C for change feedback
        if(code == 99) {
            var retVal = prompt("Enter new feedback : ", "");
            console.log(retVal)
            window.location.href = 'next?id='+id+'&change=true'+'&feedback='+encodeURIComponent(retVal);
        }

    });
});


function printAnnotatedTweet(tweet, subphrase) {
    str = "";
    console.log(subphrase);
    console.log(tweet)
    for(i=0; i<tweet.length; i++) {
        if(subphrase[i] == 'p') {
            str += "<span class=\"annotation-positive\"> " + tweet[i] + "</span> ";
        } else if(subphrase[i] == 'n') {
            str += "<span class=\"annotation-negative\"> " + tweet[i] + "</span> ";
        } else if (subphrase[i] == 'e') {
            str += "<span class=\"annotation-neutral\"> " + tweet[i] + "</span> ";
        } else {
            str += tweet[i] + " ";
        }
    }
    $("#tweet").html(str);
    if(tweet.length != subphrase.length) {
        // Do nothing
    } else {
        $("#subphrases").remove();
    }
    $("#row_id").remove();
}



