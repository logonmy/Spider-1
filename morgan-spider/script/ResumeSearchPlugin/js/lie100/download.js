/**
 * Created by wuyue on 17-7-11.
 */


var extId = $("input[name='resumeId']").val();

function act_download() {

    $("#resume_download").click(function () {
        var info = {};
        info["trackId"] = trackId;
        info["userName"] = User.userName;
        info["account"] = User.leader_email;
        info["ResumeId"] = extId;
        // alert(info);
        localStorage[extId] = JSON.stringify(info);

        var messages = {};
        messages["Message"] = "开始下载";
        messages["userName"] = User.userName;
        messages["account"] = User.leader_email;
        messages["ResumeId"] = extId;
        messages["trackId"] = trackId;
        messages["status"] = "start_download";
        messages["Target"] = "LIE_100";
        chrome.runtime.sendMessage(messages);

    });
}

function download() {
    $("#mf_action button").empty().css('background-color', '#06b5ff').attr('id', 'resume_download').html("下载简历");
    setTimeout(function () {
        act_download()
    }, 100);
}

download();
