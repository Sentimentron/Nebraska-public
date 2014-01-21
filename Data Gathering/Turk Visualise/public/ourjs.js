$(document).ready(function() {
    var subphrase = $("#subphrases").text().replace(/\s+/g, '').split("");
    var tweet = $("#tweet").text().trim().split(" ");
    printAnnotatedTweet(tweet, subphrase);

    $(document).bind('keypress', function(e) {
        var code = e.keyCode || e.which;
        if(code == 13) {
            window.location.href = 'next';
        }
        if(code == 97) {
            window.location.href = 'next?tweet='+$("#tweet").text().trim()+'&status=accept'+'&annotation='+subphrase.join("");
        }
        if(code == 114) {
            window.location.href = 'next?tweet='+$("#tweet").text().trim()+'&status=reject'+'&annotation='+subphrase.join("");
        }
        if(code == 101) {
            window.location.href = 'next?tweet='+$("#tweet").text().trim()+'&status=reject-empty'+'&annotation='+subphrase.join("");
        }
        if(code == 108) {
            window.location.href = 'next?tweet='+$("#tweet").text().trim()+'&status=reject-too-long'+'&annotation='+subphrase.join("");
        }
        if(code == 110) {
            window.location.href = 'next?tweet='+$("#tweet").text().trim()+'&status=reject-too-neutral'+'&annotation='+subphrase.join("");
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
        $("#subphrases").text("Subphrases and tweet different lengths");
    } else {
        $("#subphrases").remove();
    }
}


// $(document).click(function() {
//     window.location.href = 'next';
// });



