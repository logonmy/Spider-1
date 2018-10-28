/**
 * Created by wuyue on 17-7-11.
 */

// 隐藏下载按钮


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

    if ($(".system").html()) {
        // 以此判断简历来自 企业搜索还是猎头搜索


        // 企业搜索

        dbt = $("button[data-selector='assistant-buy']").hide();
        dbt1 = $("a[data-selector='assistant-buy']").hide();

        var s = $(".more span").html();
        var extId = s.split("|")[0].split("：")[1].replace(" ", "");

        console.log("当前简历ID: " + extId);


        var tag = document.getElementById("ResumeView_lblPostion");
        if (tag) {
            var mobile = $("td[style='white-space:nowrap;']")[1].innerText;
            if (typeof(localStorage[extId]) === "undefined") {
                // 有联系方式，不是通过下载流程过来的简历

                var messages = {};
                messages["status"] = "save_resume_0.5";
                messages["ResumeId"] = extId;
                messages["userName"] = User.userName;
                messages["Message"] = $("html").html();
                messages["Target"] = "LIE_PIN";
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
                messages["Target"] = "LIE_PIN";
                chrome.runtime.sendMessage(messages);
                localStorage.removeItem(extId);
                $("#mf_message").empty().css('color', 'green').html("简历下载成功.");

            }
        } else {
            localStorage.removeItem(extId);

            if (dbt) {
                // 添加mloading过渡页面

                $("#mf_message").empty().css('color', 'red').html("简历正在唤醒中，请耐心等待...");

                var messages = {};
                messages["status"] = "awake";
                messages["ResumeId"] = extId;
                messages["userName"] = User.userName;
                messages["Target"] = "LIE_PIN";
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
        // 猎头搜索

        dbt = $("a[data-selector='res_buy']").hide();
        var extId = $("span[data-nick='res_id']").html();
        var mobile = $(".telphone")[0];
        if (mobile) {
            var img_mobile = mobile.src;
            var img_email = $(".email")[0];

            if (img_email === undefined) {
                img_email = ''
            } else {
                img_email = img_email.src;
            }

            if (typeof(localStorage[extId]) === "undefined") {
                // 有联系方式，不是通过下载流程过来的简历
                // swal({
                //     type: "error",
                //     html: "该简历已经被下载过了",
                //     allowOutsideClick: false
                // }).then(function () {
                //     // window.close();
                //     window.opener = null;
                //     window.open('', '_self');
                //     window.close();
                // });
                submitContact(img_email, img_mobile, false);

            } else {
                submitContact(img_email, img_mobile, true);
            }
            // }
        } else {
            localStorage.removeItem(extId);

            if (dbt) {
                // 添加mloading过渡页面
                var name = $(".name").html();
                // console.log(name);
                if (name.indexOf("*") < 0) {
                    $("#mf_message").empty().css('color', 'red').html("简历正在唤醒中，请耐心等待...");
                    var messages = {};
                    messages["status"] = "awake";
                    messages["ResumeId"] = extId;
                    messages["userName"] = User.userName;
                    messages["Target"] = "LIE_PIN";
                    chrome.runtime.sendMessage(messages);
                } else {

                    swal({
                        title: "请输入该简历的姓名",
                        allowOutsideClick: false,
                        allowEscapeKey: false,
                        html: '<input name="name"' +
                        ' id="swal-name"' +
                        ' class="swal2-input" placeholder="简历姓名">',
                        preConfirm: function () {
                            return new Promise(function (resolve, reject) {
                                if (!$('#swal-name').val()) {
                                    reject('简历姓名是必填字段！！！')
                                } else {
                                    resolve([
                                        $('#swal-name').val()
                                    ])
                                }
                            })
                        },
                        onOpen: function () {
                            $('#swal-name').focus()
                        }
                    }).then(function (result) {
                        $("#mf_message").empty().css('color', 'red').html("简历正在唤醒中，请耐心等待...");

                        var messages = {};
                        messages["status"] = "awake";
                        messages["ResumeId"] = extId;
                        messages["userName"] = User.userName;
                        messages["name"] = result;
                        messages["Target"] = "LIE_PIN";
                        chrome.runtime.sendMessage(messages);
                    });
                }

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

    function submitContact(img_email, img_mobile, hasTrackId) {
        var response = {};

        if (img_email === '') {
            html = '<input name="email"' +
                ' id="swal-email"' +
                ' class="swal2-input" placeholder="邮箱" hidden><img src="' + img_mobile + '"><input' +
                ' name="phone" id="swal-mobile" class="swal2-input"' +
                ' placeholder="手机号（必填）">'
        } else {
            html = '<img src="' + img_email + '"><input name="email"' +
                ' id="swal-email"' +
                ' class="swal2-input" placeholder="邮箱"><img src="' + img_mobile + '"><input' +
                ' name="phone" id="swal-mobile" class="swal2-input"' +
                ' placeholder="手机号（必填）">'
        }

        swal({
            title: '由于联系方式为图片，后台暂时无法直接处理，请手动输入，谢谢！',
            type: 'info',
            allowOutsideClick: false,
            allowEscapeKey: false,
            html: html,
            preConfirm: function () {
                return new Promise(function (resolve, reject) {
                    if (!$('#swal-mobile').val()) {
                        reject('手机号是必填字段！！！')
                    } else if (!$("#swal-mobile").val().match(/^1[3|4|5|8][0-9]\d{4,8}$/)) {
                        reject("手机号码格式不正确！请检查！");
                    } else if (!$('#swal-email').val().match(/^\w+((-\w+)|(\.\w+))*\@[A-Za-z0-9]+((\.|-)[A-Za-z0-9]+)*\.[A-Za-z0-9]+$/)) {
                        if (!$('#swal-email').val()) {
                            resolve([
                                $('#swal-email').val(),
                                $('#swal-mobile').val()
                            ])
                        } else {
                            reject("邮箱格式不正确！请检查！");
                        }
                    } else {
                        resolve([
                            $('#swal-email').val(),
                            $('#swal-mobile').val()
                        ])
                    }
                })
            },
            onOpen: function () {
                $('#swal-email').focus()
            }
        }).then(function (result) {
            response["email"] = result[0];
            response["mobile"] = result[1];

            if (response["email"]) {
                var html1 = '<div>手机号：<span style="color:red">' + result[1] + '</span></div><div>邮箱：<span style="color:red">' + result[0] + '</span></div>'
            } else {
                var html1 = '<div>手机号：<span style="color:red">' + result[1] + '</span></div>'
            }


            swal({
                title: '联系方式确认',
                type: 'warning',
                allowOutsideClick: false,
                showCancelButton: true,
                reverseButtons: true,
                cancelButtonColor: '#d33',
                confirmButtonText: '提交',
                cancelButtonText: '重新填写',
                html: html1
            }).then(function () {
                swal({type: 'success', title: '提交成功'});
                console.log(response.email, response.mobile);
                if (hasTrackId) {
                    var info = JSON.parse(localStorage[extId]);
                    var messages = {};
                    messages["status"] = "save_resume_0.5";
                    messages["ResumeId"] = extId;
                    messages["trackId"] = info["trackId"];
                    messages["userName"] = info["userName"];
                    messages["account"] = info["account"];
                    messages["mobile"] = response.mobile;
                    messages["email"] = response.email;
                    messages["Message"] = $("html").html();
                    messages["Target"] = "LIE_PIN";
                    chrome.runtime.sendMessage(messages);
                    localStorage.removeItem(extId);
                } else {
                    var messages = {};
                    messages["status"] = "save_resume_0.5";
                    messages["ResumeId"] = extId;
                    messages["userName"] = User.userName;
                    messages["mobile"] = response.mobile;
                    messages["email"] = response.email;
                    messages["Message"] = $("html").html();
                    messages["Target"] = "LIE_PIN";
                    chrome.runtime.sendMessage(messages);
                }

            }, function (dismiss) {
                // dismiss can be 'cancel', 'overlay',
                // 'close', and 'timer'
                if (dismiss === 'cancel') {
                    submitContact(img_email, img_mobile);
                }
            })
        }).catch(swal.noop);
    }
}