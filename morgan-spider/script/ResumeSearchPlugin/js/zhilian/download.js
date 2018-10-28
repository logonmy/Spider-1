/**
 * Created by wuyue on 17-7-11.
 */


function act_download() {
    $("#resume_download").click(function () {
        var extId = $("#extId").val();
        if (extId) {
            // 老版页面
            $(".resume-preview-button.previewLayer11.smpevent")[0].click();
            $("div.szmr_sm .szmr_sm").html("");
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
            messages["Target"] = "ZHI_LIAN";
            chrome.runtime.sendMessage(messages);

            var _interval = setInterval(function () {
                var notice = $("div.szmr_sm .szmr_sm").html();
                if (notice) {
                    if (notice.indexOf("简历下载至") < 0) {
                        messages["Message"] = notice;
                        messages["status"] = "fail_download";
                        chrome.runtime.sendMessage(messages);
                    }
                    clearInterval(_interval)
                }
            }, 1000);
        } else {
            extId = $('.r-resume-time .fl .color-999').html();
            // console.log(extId);
            document.getElementById("downloadResumeBtn").click();
            // $("#downloadResumeBtn").click();

            info = {};
            info["trackId"] = trackId;
            info["userName"] = User.userName;
            info["account"] = User.leader_email;
            info["ResumeId"] = extId;
            // alert(info);
            localStorage[extId] = JSON.stringify(info);

            messages = {};
            messages["Message"] = "开始下载";
            messages["userName"] = User.userName;
            messages["account"] = User.leader_email;
            messages["ResumeId"] = extId;
            messages["trackId"] = trackId;
            messages["status"] = "start_download";
            messages["Target"] = "ZHI_LIAN";
            chrome.runtime.sendMessage(messages);

            _interval = setInterval(function () {
                var notice = $("div.szmr_sm .szmr_sm").html();
                if (notice) {
                    if (notice.indexOf("简历下载至") < 0) {
                        messages["Message"] = notice;
                        messages["status"] = "fail_download";
                        chrome.runtime.sendMessage(messages);
                    }
                    clearInterval(_interval)
                }
            }, 1000);
        }
    });
}

function download() {
    $("#mf_action button").empty().css('background-color', '#06b5ff').attr('id', 'resume_download').html("下载简历");
    setTimeout(function () {
        act_download()
    }, 100);
}

download();
