/**
 * Created by wuyue on 17-7-11.
 */

// 隐藏下载按钮

dbt = document.getElementsByClassName("btn btn-warning")[0];
dbt1 = document.getElementsByClassName("btn btn-warning")[1];


var extId = $("input[name='resumeId']").val();

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

    localStorage.removeItem(extId);

    if (dbt) {
        // 添加mloading过渡页面
        dbt.style.display = 'none';
        dbt1.style.display = 'none';

        $("#mf_message").empty().css('color', 'red').html("简历正在唤醒中，请耐心等待...");
        var messages = {};
        messages["status"] = "awake";
        messages["ResumeId"] = extId;
        messages["userName"] = User.userName;
        messages["Target"] = "LIE_100";
        chrome.runtime.sendMessage(messages);
        console.log('base.js--=>>>>>>' + JSON.stringify(messages))
    } else {
        // alert("链接失效了")
        swal({type: "error", html: "链接失效了", timer: 2000}).then(function () {
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

