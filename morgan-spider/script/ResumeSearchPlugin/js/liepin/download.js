/**
 * Created by wuyue on 17-7-11.
 */


if ($(".system").html()) {
    // 以此判断简历来自 企业搜索还是猎头搜索

    // 企业搜索

    var s = $(".more span").html();
    var extId = s.split("|")[0].split("：")[1].replace(" ", "");
    download("qy");
} else {
    // 猎头搜索

    var extId = $("span[data-nick='res_id']").html();
    download("lt");
}


function act_download(search_type) {

    $("#resume_download").click(function () {
        if (search_type === "lt") {
            $("a[data-selector='res_buy']")[0].click();
        }
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
        messages["Target"] = "LIE_PIN";
        chrome.runtime.sendMessage(messages);
    });
}

function download(search_type) {
    if (search_type === "qy") {

    } else if ((search_type === "lt")) {
        $("#mf_action button").empty().css('background-color', '#06b5ff').attr('id', 'resume_download').html("下载简历");
    }

    setTimeout(function () {
        act_download(search_type)
    }, 100);
}