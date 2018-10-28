/**
 * Created by wuyue on 17-7-11.
 */

// 隐藏下载按钮


function save_resume() {
    if (typeof(localStorage[extId]) === "undefined") {
        // 有联系方式，不是通过下载流程过来的简历
        var messages = {};
        messages["status"] = "save_resume_0.5";
        messages["ResumeId"] = extId;
        messages["userName"] = User.userName;
        messages["mobile"] = mobile;
        messages["Message"] = $("html").html();
        messages["Target"] = "ZHI_LIAN";
        chrome.runtime.sendMessage(messages);
        $("#mf_message").empty().css('color', 'red').html("该简历已经被下载过了.");

    } else {
        var info = JSON.parse(localStorage[extId]);
        messages = {};
        messages["status"] = "save_resume_0.5";
        messages["ResumeId"] = extId;
        messages["trackId"] = info["trackId"];
        messages["userName"] = info["userName"];
        messages["account"] = info["account"];
        messages["mobile"] = mobile;
        messages["Message"] = $("html").html();
        messages["Target"] = "ZHI_LIAN";
        chrome.runtime.sendMessage(messages);
        localStorage.removeItem(extId);
        $("#mf_message").empty().css('color', 'green').html("简历下载成功.");
    }
}


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
}


// RD2版本extId获取
var extId = $("#extId").val();

if (extId) {
    var userName = document.getElementById("userName");

    if (userName) {
        var mobile = $("b").eq(1).html();
        save_resume();
    } else {
        localStorage.removeItem(extId);
        var dbt = document.getElementsByClassName("resume-preview-button previewLayer11 smpevent")[0];
        var dbt2 = document.getElementsByClassName("previewLayer11 rd_button" +
            " smpevent")[0];

        if (dbt) {
            // 添加mloading过渡页面
            dbt.hidden = true;
            dbt2.hidden = true;

            $("#mf_message").empty().css('color', 'red').html("简历正在唤醒中，请耐心等待...");
            var messages = {};
            messages["status"] = "awake";
            messages["ResumeId"] = extId;
            messages["userName"] = User.userName;
            messages["Target"] = "ZHI_LIAN";
            messages["is_check"] = true;
            messages["position"] = ".summary-top";

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
} else {
    _interval_ext = setInterval(function () {
        extId = $('.r-resume-time .fl .color-999').html();
        // console.log(extId);

        if (extId) {
            clearInterval(_interval_ext);

            if ($('.currentStatusTxt').html() !== undefined) {
                // 0.5简历上传
                mobile = $('.telephone').text().split('：')[1];
                save_resume()
            } else {
                var i = 0;
                _interval_download = setInterval(function () {
                    // 通过轮询获取下载按钮 重试10次
                    var dbt = document.getElementById('downloadResumeBtn');
                    // console.log(dbt);

                    if (dbt) {
                        clearInterval(_interval_download);
                        // 添加mloading过渡页面
                        dbt.style = 'display: none';

                        $("#mf_message").empty().css('color', 'red').html("简历正在唤醒中，请耐心等待...");
                        messages = {};
                        messages["status"] = "awake";
                        messages["ResumeId"] = extId;
                        messages["userName"] = User.userName;
                        messages["Target"] = "ZHI_LIAN";
                        messages["is_check"] = true;
                        messages["position"] = ".portraitStatusContainer";

                        chrome.runtime.sendMessage(messages);
                        console.log('base.js--=>>>>>>' + JSON.stringify(messages))
                    } else {
                        if (i < 10) {
                            i++;
                        } else {
                            clearInterval(_interval_download);
                        }
                    }
                }, 100);
                // console.log(dbt);

                if ($(".userNameContainer").html() !== '') {

                    $("#mf_message").empty().css('color', 'red').html("该简历智联不提供下载.");
                    messages = {};
                    messages["status"] = "awake";
                    messages["ResumeId"] = extId;
                    messages["userName"] = User.userName;
                    messages["Target"] = "ZHI_LIAN";
                    messages["is_check"] = false;
                    messages["position"] = ".portraitStatusContainer";

                    chrome.runtime.sendMessage(messages);
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
        } else {
            $("#mf_message").empty().css('color', 'red').html("页面加载中，请耐心等待...");
        }

    }, 100);

}

