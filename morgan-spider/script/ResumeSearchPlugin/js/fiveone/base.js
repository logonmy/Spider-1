/**
 * Created by wuyue on 17-7-11.
 */

// 隐藏下载按钮

dbt = document.getElementById("RersumeView_btnDownLoad_link");
dbt1 = document.getElementById("UndownloadLink");
dbt2 = document.getElementsByClassName("rself_listoff")[1];

var extId = $("#hidUserID").val();

if (typeof(User) === "undefined") {
    swal({
        type: "warning",
        title: "未选择您的身份",
        html: "请点击右上角的插件图标，设置你的身份！",
        allowOutsideClick: false,
        allowEscapeKey: false
    }).then(function () {
        location.reload();
    })
} else {

    var mobile = $("td[style='white-space:nowrap;']")[1];
    if (mobile) {
        mobile = mobile.innerText;
        if (typeof(localStorage[extId]) === "undefined") {
            // 有联系方式，不是通过下载流程过来的简历

            var messages = {};
            messages["status"] = "save_resume_0.5";
            messages["ResumeId"] = extId;
            messages["userName"] = User.userName;
            messages["mobile"] = mobile;
            messages["Message"] = $("html").html();
            messages["Target"] = "FIVE_ONE";
            chrome.runtime.sendMessage(messages);
            $("#mf_message").empty().css('color', 'red').html("该简历已经被下载过了.");

        } else {
            var info = JSON.parse(localStorage[extId]);
            var messages = {};
            messages["status"] = "save_resume_0.5";
            messages["ResumeId"] = extId;
            messages["trackId"] = info["trackId"];
            messages["userName"] = info["userName"];
            messages["account"] = info["account"];
            messages["mobile"] = mobile;
            messages["Message"] = $("html").html();
            messages["Target"] = "FIVE_ONE";
            chrome.runtime.sendMessage(messages);
            localStorage.removeItem(extId);
            $("#mf_message").empty().css('color', 'green').html("简历下载成功.");

        }
    } else {

        localStorage.removeItem(extId);

        if (dbt) {
            // 添加mloading过渡页面
            dbt.style.display = 'none';
            dbt1.style.display = 'none';
            dbt2.hidden = true;

            $("#mf_message").empty().css('color', 'red').html("简历正在唤醒中，请耐心等待...");
            var messages = {};
            messages["status"] = "awake";
            messages["ResumeId"] = extId;
            messages["userName"] = User.userName;
            messages["Target"] = "FIVE_ONE";
            chrome.runtime.sendMessage(messages);
            console.log('base.js--=>>>>>>' + JSON.stringify(messages))
        } else {
            // alert("链接失效了")
            swal({
                type: "error",
                html: "链接失效了",
                timer: 2000
            }).then(function () {
                // window.close();
                window.opener = null;
                window.open('', '_self');
                window.close();
            }, function (dismiss) {
                if (dismiss === 'timer') {
                    window.opener = null;
                    window.open('', '_self');
                    window.close();
                }
            });
        }
    }
}