/**
 * Created by wuyue on 17-7-11.
 */


var extId = $("#hidUserID").val();

function act_download() {

    $("#resume_download").click(function () {
        $("#p_resumeMsgbox div[style='color:#FF0000;']").html("");
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
        messages["Target"] = "FIVE_ONE";
        chrome.runtime.sendMessage(messages);

        var _interval = setInterval(function () {
            var notice = $("#p_resumeMsgbox div[style='color:#FF0000;']").html();
            if (notice) {
                messages["Message"] = notice;
                messages["status"] = "fail_download";
                chrome.runtime.sendMessage(messages);
                clearInterval(_interval)
            }
        }, 1000);

    });
}

function download() {

    $("#mf_action button").empty().css('background-color', '#06b5ff').attr('id', 'resume_download').attr('onclick', 'return InboxEngine.OpenResumeCommonLayer("DownLoad",null,null,1);').html("下载简历");
    setTimeout(function () {
        act_download()
    }, 100);
}

download();
