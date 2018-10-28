/**
 * Created by wuyue on 17-7-12.
 */

window.onload = (function () {
    if (localStorage["mofang_switch"] === undefined) {
        localStorage["mofang_switch"] = true;
        $("#switch").html("on");
    }else if (localStorage["mofang_switch"] === "true") {
        $("#switch").html("on");
    } else {
        $("#switch").html("off");
    }
    init_config("ZHI_LIAN");
    init("ZHI_LIAN");
    inputManager("ZHI_LIAN");
});


var sites = ['ZHI_LIAN', 'FIVE_ONE', 'LIE_100', 'LIE_PIN'];

// 插件开关


$("#switch").click(function () {
    if (localStorage["mofang_switch"] === "true") {
        localStorage["mofang_switch"] = false;
        $(this).html("off");
        console.log("mofang_switch " + localStorage.mofang_switch)
    } else if (localStorage["mofang_switch"] = "false") {
        localStorage["mofang_switch"] = true;
        console.log("mofang_switch " + localStorage.mofang_switch);
        $(this).html("on");
    } else {
        localStorage.mofang_switch = true;
        $(this).html("on");
    }
});

// // 获取所有的总监-账号绑定信息
// var get_crm_account_url = "http://10.0.4.199:8102/crm/getCrmAccount";
// //根据总监id获取可以分配的用户id
// var get_crm_user_url = "http://10.0.4.199:8102/crm/getCrmUser";
//
// var crm_score_download_url = "http://10.0.4.199:8102/crm/downloadScore";
// var crm_score_url = "http://10.0.4.199:8102/crm/score";

// 获取所有的总监-账号绑定信息
var get_crm_account_url = "http://morgan-parse.mofanghr.com/crm/getCrmAccount";
//根据总监id获取可以分配的用户id
var get_crm_user_url = "http://morgan-parse.mofanghr.com/crm/getCrmUser";

var crm_score_download_url = "http://morgan-parse.mofanghr.com/crm/downloadScore";
var crm_score_url = "http://morgan-parse.mofanghr.com/crm/score";


function init_config(source) {
    var user = localStorage[source + '_ASSIGNED_USER'];
    $(".help-block." + source).html("");
    if (typeof(user) === "undefined") {
        $("#config_" + source).empty().html("未设置");
    } else {
        var userName = JSON.parse(user).userName;
        var score_download = crmScore(crm_score_download_url, userName, source);
        var score = crmScore(crm_score_url, userName, '');
        console.log(score, score_download);

        if (score_download === "" || score_download === null) {
            $("#config_" + source).empty().addClass("text-danger").html("服务器连接异常！当日下载剩余额度查询失败");
        } else if (score === "" || score === null) {
            $("#config_" + source).empty().addClass("text-danger").html("服务器连接异常！当前分配剩余额度查询失败");
        } else {
            $("#config_" + source).empty().removeClass("text-danger").html("绑定用户：" + userName + "<br>当日下载剩余额度：" + JSON.parse(score_download) + "<br>当前分配剩余额度：" + JSON.parse(score));
        }
    }
}


function inputManager(source) {
    var leader_email;
    $("#leader_" + source).change(function () {
        var val = $(this).val();
        // var data = {'sj': val};
        var result = getUser(get_crm_user_url, val);
        console.log(JSON.stringify(result));
        var html = "<option value='0'>-请选择你是谁-</option>";
        for (var i = 0; i < result.length; i++) {
            var data = result[i];
            html += "<option value='" + data.realName + "'>" + data.realName + "</option>";
        }
        $("#user_" + source).empty().append(html);
        leader_email = val;
    });
    $("#save_" + source).click(function () {
        var userId = $("#user_" + source).val();
        if (userId === '0') {
            $(".help-block").html("你没有选择正确的user!")
        } else {
            var userName = $("#user_" + source + " option:selected").text();
            var data = {'userName': userName, 'leader_email': leader_email};
            for (var item in sites) {
                window.localStorage.setItem(sites[item] + "_ASSIGNED_USER", JSON.stringify(data));
                console.log("当前设置：" + window.localStorage.getItem(sites[item] + "_ASSIGNED_USER"));
            }
            // window.localStorage.setItem(source + "_ASSIGNED_USER", JSON.stringify(data));
            // console.log("当前设置：" + window.localStorage.getItem(source + "_ASSIGNED_USER"));
            init_config(source);
            $(".help-block." + source).html("保存成功");
        }
    });
}

function init(source) {
    var zjs = getAccount(get_crm_account_url, source);
    console.log(JSON.stringify(zjs));
    // console.log(zjs);
    var html = "<option value='0'>-请选择你的Leader-</option>";
    for (var i = 0; i < zjs.length; i++) {
        var data = zjs[i];
        html += "<option value='" + data.email + "'>" + data.name + "</option>";
    }
    $("#leader_" + source).empty().append(html);

}

function crmScore(url, userName, source) {
    var result = "";
    $.ajax({
        url: url,
        data: {
            userName: userName,
            source: source
        },
        type: "post",
        dataType: "json",
        async: false,
        success: function (response_data) {
            if (response_data.code === 200) {
                result = response_data.data;
            } else {
                $("#config_" + source).empty().addClass("text-danger").html(response_data.msg);
            }
            console.log("额度查询结果:" + url + " " + JSON.stringify(response_data))
        }
    });
    return result;
}

function getAccount(url, source) {
    var obj;
    $.ajax({
        url: url,
        type: "post",
        data: {
            source: source
        },
        dataType: "json",
        async: false,
        success: function (response_data) {
            if (response_data.code === 200) {
                obj = response_data.data;
            } else {
                $("#config_" + source).empty().addClass("text-danger").html(response_data.msg);
            }
            console.log("leader查询结果:" + JSON.stringify(obj));
        }
    });
    return obj;
}

function getUser(url, email) {
    var obj;
    $.ajax({
        url: url,
        type: "post",
        data: {
            email: email
        },
        dataType: "json",
        async: false,
        success: function (response_data) {
            if (response_data.code === 200) {
                obj = response_data.data;
                console.log("users查询结果:" + JSON.stringify(obj));
            } else {
                $("#config_" + source).empty().addClass("text-danger").html(response_data.msg);
            }
        }
    });
    return obj;
}

$('a[href="#zhilian"]').click(function () {
    init_config("ZHI_LIAN");
    init("ZHI_LIAN");
    inputManager("ZHI_LIAN");
});

$('a[href="#fiveone"]').click(function () {
    init_config("FIVE_ONE");
    init("FIVE_ONE");
    inputManager("FIVE_ONE");
});

$('a[href="#lie100"]').click(function () {
    init_config("LIE_100");
    init("LIE_100");
    inputManager("LIE_100");
});

$('a[href="#liepin"]').click(function () {
    init_config("LIE_PIN");
    init("LIE_PIN");
    inputManager("LIE_PIN");
});


// 监听localstorage
// var orignalSetItem = localStorage.setItem;
// localStorage.setItem = function (key, newValue) {
//     var setItemEvent = new Event("setItemEvent");
//     setItemEvent.key = key;
//     setItemEvent.newValue = newValue;
//     window.dispatchEvent(setItemEvent);
//     orignalSetItem.apply(this, arguments);
// };
//
//
// window.addEventListener("setItemEvent", function (e) {
//     if (e.key.indexOf('_ASSIGNED_USER')) {
//         console.log(e.key);
//         var messages = {};
//         messages["Message"] = "配置文件被修改了";
//         messages["status"] = "update_config";
//         messages["Target"] = e.key.replace('_ASSIGNED_USER', '');
//         chrome.runtime.sendMessage(messages);
//     }
// });