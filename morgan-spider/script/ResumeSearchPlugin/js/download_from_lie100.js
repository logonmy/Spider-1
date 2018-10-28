/**
 * Created by wuyue on 17-8-18.
 */


function act_download() {

    $("#resume_download_from_lie100").click(function () {
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
        messages["ResumeId"] = lie100_id;
        messages["trackId"] = trackId;
        messages["position"] = position;
        messages["callpath"] = callpath;
        messages["source"] = source;
        messages["status"] = "start_download_from_lie100";
        messages["Target"] = "LIE_100";
        messages["distributeSource"] = Target;
        chrome.runtime.sendMessage(messages);

    });
}

function download() {
    $("#mf_action button").empty().css('background-color', '#06b5ff').attr('id', 'resume_download_from_lie100').html("下载简历(有本)");
    // $("#mf_action button").empty().css('background-color', '#06b5ff').attr('id', 'resume_download').html("下载简历");
    setTimeout(function () {
        act_download()
    }, 100);
}

download();
