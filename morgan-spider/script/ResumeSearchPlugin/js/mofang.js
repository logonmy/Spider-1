/**
 * Created by wuyue on 17-7-6.
 */

// product_domain
var start_awake_url = "http://morgan-parse.mofanghr.com/crm/parse.json";
var start_lie100_awake_url = "http://morgan-youben.mofanghr.com/resume/detail";
var download_lie100_resume_url = "http://morgan-youben.mofanghr.com/resume/buy";
var check_awake_url = "http://morgan-pick.mofanghr.com/crm/checkBuy";
var save_flow_url = "http://morgan-parse.mofanghr.com/crm/addFlow.json";
var check_crm_distribute_url = "http://morgan-parse.mofanghr.com/crm/checkDistribute";
var force_crm_distribute_url = "http://morgan-parse.mofanghr.com/crm/forceDistribute";
var check_crm_score_url = "http://morgan-parse.mofanghr.com/crm/score";
var check_score_download_url = "http://morgan-parse.mofanghr.com/crm/downloadScore";

// product
// var start_awake_url = "http://172.16.25.43:8102/crm/parse.json";
// var start_lie100_awake_url = "http://172.16.25.43:8212/resume/detail";
// var download_lie100_resume_url = "http://172.16.25.43:8212/resume/buy";
// var check_awake_url = "http://172.16.25.43:8104/crm/checkBuy";
// var save_flow_url = "http://172.16.25.43:8102/crm/addFlow.json";
// var check_crm_distribute_url = "http://172.16.25.43:8102/crm/checkDistribute";
// var force_crm_distribute_url = "http://172.16.25.43:8102/crm/forceDistribute";
// var check_crm_score_url = "http://172.16.25.43:8102/crm/score";
// var check_score_download_url = "http://172.16.25.43:8102/crm/downloadScore";

// dev
// var start_awake_url = "http://10.0.4.199:8102/crm/parse.json";
// var start_lie100_awake_url = "http://10.0.4.199:8212/resume/detail";
// var download_lie100_resume_url = "http://10.0.4.199:8212/resume/buy";
// var check_awake_url = "http://10.0.4.199:8104/crm/checkBuy";
// var save_flow_url = "http://10.0.4.199:8102/crm/addFlow.json";
// var check_crm_distribute_url = "http://10.0.4.199:8102/crm/checkDistribute";
// var force_crm_distribute_url = "http://10.0.4.199:8102/crm/forceDistribute";
// var check_crm_score_url = "http://10.0.4.199:8102/crm/score";
// var check_score_download_url = "http://10.0.4.199:8102/crm/downloadScore";


function startAwake(target, data, resourceType, mobile, trackId, userName, email, name) {
    if (userName == null || userName == "undefined") {
        userName = JSON.parse(localStorage[target + "_ASSIGNED_USER"]).userName;
        // console.log(userName)
    }
    var result = "";
    $.ajax({
        url: start_awake_url,
        type: "post",
        data: {
            'content': data,
            'source': target,
            'resourceType': resourceType,
            'mobile': mobile,
            'flowNo': trackId,
            'userName': userName,
            'email': email,
            'name': name
        },
        dataType: "json",
        async: false,
        success: function (response_data) {
            result = response_data;
            console.log("简历推送结果:" + JSON.stringify(response_data))
        }
    });
    return result;
}

function startLie100Awake(userName, resumeId) {
    var result = "";
    $.ajax({
        url: start_lie100_awake_url,
        type: "post",
        data: {
            'userName': userName,
            'resumeId': resumeId
        },
        dataType: "json",
        async: false,
        success: function (response_data) {
            result = response_data;
            console.log("lie100简历ID推送结果:" + JSON.stringify(response_data))
        }
    });
    return result;
}

function downloadLie100Resume(userName, resumeId, callType) {
    var result = "";
    $.ajax({
        url: download_lie100_resume_url,
        type: "post",
        data: {
            'userName': userName,
            'resumeId': resumeId,
            'callType': callType
        },
        dataType: "json",
        async: false,
        success: function (response_data) {
            result = response_data;
            console.log("lie100简历下载结果:" + JSON.stringify(response_data))
        }
    });
    return result;
}

function checkAwake(target, trackId) {
    var result = "";
    $.ajax({
        url: check_awake_url + '?trackId=' + trackId + '&source=' + target,
        type: "get",
        dataType: "json",
        async: false,
        success: function (response_data) {
            result = response_data;
            console.log("简历check结果:" + JSON.stringify(response_data))
        }
    });
    return result;
}

function saveFlow(flowNo, code, message, userName, resumeId, source, account, mobile, distributeSource) {
    var result = "";
    $.ajax({
        url: save_flow_url,
        data: {
            flowNo: flowNo,
            code: code,
            message: message,
            userName: userName,
            resumeId: resumeId,
            source: source,
            account: account,
            mobile: mobile,
            distributeSource: distributeSource
        },
        type: "post",
        dataType: "json",
        async: false,
        success: function (response_data) {
            result = response_data;
            console.log("流水添加结果:" + JSON.stringify(response_data))
        }
    });
    return result;
}

function checkCrmDistribute(mobile) {
    var result = "";
    $.ajax({
        url: check_crm_distribute_url,
        data: {
            mobile: mobile
        },
        type: "post",
        dataType: "json",
        async: false,
        success: function (response_data) {
            result = response_data;
            console.log("简历分配结果:" + JSON.stringify(response_data))
        }
    });
    return result;
}

function forceCrmDistribute(userName, resumeId) {
    var result = "";
    $.ajax({
        url: force_crm_distribute_url,
        data: {
            resumeId: resumeId,
            userName: userName
        },
        type: "post",
        dataType: "json",
        async: false,
        success: function (response_data) {
            result = response_data;
            console.log("crm强分配结果:" + JSON.stringify(response_data))
        }
    });
    return result;
}

function checkScoreDownload(userName, source) {
    var result = "";
    $.ajax({
        url: check_score_download_url,
        data: {
            userName: userName,
            source: source
        },
        type: "post",
        dataType: "json",
        async: false,
        success: function (response_data) {
            result = response_data;
            console.log("下载额度查询结果:" + JSON.stringify(response_data))
        }
    });
    return result;
}

function checkCrmScore(userName, source) {
    var result = "";
    $.ajax({
        url: check_crm_score_url,
        data: {
            userName: userName,
            source: source
        },
        type: "post",
        dataType: "json",
        async: false,
        success: function (response_data) {
            result = response_data;
            console.log("剩余额度查询结果:" + JSON.stringify(response_data))
        }
    });
    return result;
}


function saveResume(tabId, messages) {
    // 0.5 简历处理
    startAwake(messages.Target, messages.Message.toString(), "RESUME_INBOX", messages.mobile, messages.trackId, messages.userName);
    if (messages.trackId) {
        saveFlow(messages.trackId, "104", "下载成功", messages.userName, messages.ResumeId, messages.Target, messages.account, messages.mobile);
    } else {
        // console.log(messages);
        var ret = checkCrmDistribute(messages.mobile);
        console.log(ret);
        if (ret.code === 100) {
            console.log(ret);
            chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "手机号为(' + messages.mobile + ')的简历已在[' + ret.data.name + ']名下.");'})
        } else if (ret.code === 200) {

            var score_download = checkScoreDownload(messages.userName, messages.Target);
            if (score_download.code === 200) {
                if (score_download.data <= 0) {
                    chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "您的当日简历下载量已达到限额，暂时不能将此简历分配到您的名下.");'})
                } else {
                    var score = checkCrmScore(messages.userName, messages.Target);
                    // var score = 0;
                    if (score.code === 200) {
                        if (score.data <= 0) {
                            chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "crm系统中，您名下的简历已达到限额，暂时不能将此简历分配到您的名下.");'})
                        } else {
                            chrome.tabs.executeScript(tabId, {
                                code: 'var' +
                                ' crm_resumeId="' + ret.data.resumeId + '";updateMessage("green", "该简历尚未被分配，是否分配到你(' + messages.userName + ')的名下？");$("#mf_action button").empty().css("background-color", "#06b5ff").attr("id", "mf_distribute").html("分配到我名下");$("#mf_distribute").click(function(){chrome.runtime.sendMessage({"Target":"' + messages.Target + '","status":"assigned", "Message":crm_resumeId})});'
                            });
                        }
                    } else {
                        chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "crm额度查询异常, ' + score.msg + '");'});
                    }
                }
            } else {
                chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "morgan额度查询异常, ' + score_download.msg + '");'});
            }

        } else {
            chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "简历分配校验异常.");'});
        }
    }
    console.log("上传成功 0.5 -> " + messages.Target + " " + messages.ResumeId);
}


function doAwakeSuccess(tabId, response, messages, callpath, position) {
    // 唤醒成功
    var ret = checkCrmDistribute(response.data.mobile);
    if (ret.code === 100) {
        chrome.tabs.executeScript(tabId, {code: 'updateMessage("red","手机号为(' + response.data.mobile + ')的简历已在[' + ret.data.name + ']名下.");'})
    } else if (ret.code === 200) {
        var score_download = checkScoreDownload(messages.userName, messages.Target);
        if (score_download.code === 200) {
            if (score_download.data <= 0) {
                chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "您的当日简历下载量已达到限额，暂时不能将此简历分配到您的名下.");'})
            } else {
                var score = checkCrmScore(messages.userName, messages.Target);

                if (score.code === 200) {
                    if (score.data <= 0) {
                        chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "crm系统中，您名下的简历已达到限额，暂时不能将此简历分配到您的名下.");'})
                    } else {
                        if (position) {
                            chrome.tabs.executeScript(tabId, {
                                code: 'var' +
                                ' crm_resumeId="' + ret.data.resumeId + '";var html =' +
                                ' \'<br><span style="color:red;font-size:24px;">' + response.data.name + ' | ' + response.data.mobile + ' | ' + response.data.email + '</span><br><br>\';$("' + callpath + '").prepend(html);updateMessage("green", "唤醒成功，该简历尚未被分配，是否分配到你(' + messages.userName + ')的名下？");$("#mf_action button").empty().css("background-color", "#06b5ff").attr("id", "mf_distribute").html("分配到我名下");$("#mf_distribute").click(function(){chrome.runtime.sendMessage({"Target":"' + messages.Target + '","status":"assigned", "Message":crm_resumeId})});'
                            });
                        } else {
                            chrome.tabs.executeScript(tabId, {
                                code: 'var' +
                                ' crm_resumeId="' + ret.data.resumeId + '";var html =' +
                                ' \'<br><span style="color:red;font-size:24px;">' + response.data.name + ' | ' + response.data.mobile + ' | ' + response.data.email + '</span><br><br>\';$("' + callpath + '").append(html);updateMessage("green", "唤醒成功，该简历尚未被分配，是否分配到你(' + messages.userName + ')的名下？");$("#mf_action button").empty().css("background-color", "#06b5ff").attr("id", "mf_distribute").html("分配到我名下");$("#mf_distribute").click(function(){chrome.runtime.sendMessage({"Target":"' + messages.Target + '","status":"assigned", "Message":crm_resumeId})});'
                            });
                        }
                    }
                } else {
                    chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "crm额度查询异常, ' + score.msg + '");'});
                }
            }
        } else {
            chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "morgan额度查询异常, ' + score_download.msg + '");'});
        }

    } else {
        chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "简历分配校验异常.");'});
    }
    console.log("唤醒成功 ->" + messages.Target + " " + messages.ResumeId)
}


function doAwakeSuccessFromLie100(tabId, response, messages, trackId, source, callpath, position) {
    // 唤醒成功 From lie100
    var score_download = checkScoreDownload(messages.userName, messages.Target);
    if (score_download.code === 200) {
        if (score_download.data <= 0) {
            chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "您的当日简历下载量已达到限额，暂时不能将此简历分配到您的名下.");'})
        } else {
            var score = checkCrmScore(messages.userName, messages.Target);

            if (score.code === 200) {
                if (score.data <= 0) {
                    chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "crm系统中，您名下的简历已达到限额，暂时不能将此简历分配到您的名下.");'})
                } else {
                    chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "简历唤醒失败，在有本找到相匹配的简历，请点击“下载简历(有本)”.");'});
                    chrome.tabs.executeScript(tabId, {
                        code: 'var' +
                        ' position=' + position + ';var callpath="' + callpath + '";var lie100_id="' + response.data + '";var trackId="'+trackId+'";var Target="'+messages.Target+'";var source="'+source+'";'
                    });
                    chrome.tabs.executeScript(tabId, {file: 'js/download_from_lie100.js'})
                }
            } else {
                chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "crm额度查询异常, ' + score.msg + '");'});
            }
        }
    } else {
        chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "morgan额度查询异常, ' + score_download.msg + '");'});
    }
}

function doAwakeFailed(tabId, messages, trackId, source) {
    var score_download = checkScoreDownload(messages.userName, messages.Target);
    if (score_download.code === 200) {
        if (score_download.data <= 0) {
            chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "您的当日简历下载量已达到限额，暂时不能下载更多的简历.");'})
        } else {
            var score = checkCrmScore(messages.userName, messages.Target);

            if (score.code === 200) {
                if (score.data <= 0) {
                    chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "crm系统中，您名下的简历已达到限额，暂时不能下载更多的简历.");'})
                } else {
                    chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "简历唤醒失败，确认需要该简历，请点击“下载简历”.");'});
                    console.log("唤醒失败 ->" + messages.ResumeId);
                    chrome.tabs.executeScript(tabId, {code: 'var trackId="' + trackId + '"'});
                    chrome.tabs.executeScript(tabId, {file: 'js/' + source + '/download.js'});
                }
            } else {
                chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "crm额度查询异常, ' + score.msg + '");'});
            }
        }
    } else {
        chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "morgan额度查询异常, ' + score_download.msg + '");'});
    }

}

function assignedResume(tabId, messages) {
    var userName = JSON.parse(localStorage[messages.Target + '_ASSIGNED_USER']).userName;
    var ret = forceCrmDistribute(userName, messages.Message);
    if (ret.code === 200) {
        chrome.tabs.executeScript(tabId, {
            code: 'updateMessage("green",' +
            ' "简历分配结果：' + ret.msg + '");$("#mf_action' +
            ' button").empty().css("background-color",' +
            ' "").removeAttr("id").off().html("不可用")'
        });
    } else {
        chrome.tabs.executeScript(tabId, {
            code: 'updateMessage("red",' +
            ' "简历分配结果：' + ret.msg + '");$("#mf_action' +
            ' button").empty().css("background-color",' +
            ' "").removeAttr("id").off().html("不可用")'
        });
    }

    console.log("简历分配：" + messages.Target + " " + messages.Message + " " + userName);
}


var map = {};

var RETRY = 60;


function callback(tabId, info) {
    if (info.status === "complete" && localStorage.mofang_switch === "true") {
        chrome.tabs.query({
            'active': true,
            // 'lastFocusedWindow': true
            'currentWindow': true
        }, function (tabs) {

            if (map[tabId] === undefined || map[tabId] === '') {
                map[tabId] = '1';

                chrome.runtime.onMessage.addListener(function (messages, sender, sendResponse) {
                        // alert(JSON.stringify(messages))

                        if (sender.tab.id === tabId) {
                            if (messages.Target === "ZHI_LIAN") {
                                if (messages.status === "save_resume_0.5") {
                                    saveResume(tabId, messages);
                                } else if (messages.status === "awake") {
                                    chrome.tabs.executeScript(null, {
                                        code: '$("html").html();'
                                    }, function (data) {
                                        // console.log(tabId);
                                        var res = startAwake(messages.Target, data.toString(), "CRM_SEARCH");
                                        console.log("上传成功 0.1 -> " + messages.ResumeId);
                                        if (messages.is_check===true) {
                                            if (res) {
                                                if (res.code === 200) {
                                                    var i = 1;
                                                    var _interval;
                                                    var trackId = res.data;
                                                    _interval = setInterval(function () {
                                                        i++;

                                                        if (i < RETRY) {
                                                            chrome.tabs.get(tabId, function () {
                                                                if (chrome.runtime.lastError) {
                                                                    console.log("窗口已经被关闭了：" + chrome.runtime.lastError.message);
                                                                    clearInterval(_interval);
                                                                }
                                                            });
                                                            var response = checkAwake(3, trackId);

                                                            if (response) {
                                                                // response.code = 107;
                                                                // response.data = 'fdsafsf';
                                                                if (response.code === 200) {
                                                                    clearInterval(_interval);
                                                                    doAwakeSuccess(tabId, response, messages, messages.position);
                                                                } else if (response.code === 107) {
                                                                    clearInterval(_interval);
                                                                    doAwakeSuccessFromLie100(tabId, response, messages, trackId, 'zhilian', messages.position)
                                                                } else if (response.code === 100) {
                                                                    clearInterval(_interval);
                                                                    doAwakeFailed(tabId, messages, trackId, 'zhilian');

                                                                } else {
                                                                    var cost = i * 5;
                                                                    // chrome.tabs.executeScript(tabId, {code: '$(".mloading-text").html("' + cost + '秒过去啦...")'});
                                                                    chrome.tabs.executeScript(tabId, {code: '$("#mf_message").html("' + cost + '秒过去啦...")'});
                                                                }
                                                            } else {
                                                                clearInterval(_interval);
                                                                chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "无法连接到唤醒服务器[pick]。请联系管理员！");'});
                                                            }
                                                        } else {
                                                            clearInterval(_interval);
                                                            chrome.tabs.executeScript(tabId, {
                                                                code: 'updateMessage("red", "啊呀，唤醒超时了！！！请稍后再试。");'
                                                            })
                                                        }
                                                    }, 5000);
                                                } else if (res.code === 500) {
                                                    chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "' + res.msg + '");'})
                                                } else {
                                                    chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "唤醒服务器异常。code：！' + res.code + '");'});
                                                }
                                            } else {
                                                chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "无法连接到唤醒服务器[parse]。请联系管理员！");'});
                                            }
                                        }
                                    });
                                } else if (messages.status === "start_download") {
                                    saveFlow(messages.trackId, "103", messages.Message, messages.userName, messages.ResumeId, messages.Target, messages.account, messages.mobile);
                                    console.log("开始下载 -> " + messages.ResumeId);

                                } else if (messages.status === "fail_download") {
                                    saveFlow(messages.trackId, "105", messages.Message, messages.userName, messages.ResumeId, messages.Target, messages.account, messages.mobile);
                                    console.log("下载失败 -> " + messages.ResumeId + " Message: " + messages.Message);
                                } else if (messages.status === "assigned") {
                                    assignedResume(tabId, messages);
                                }


                            } else if (messages.Target === "FIVE_ONE") {
                                // 前程
                                if (messages.status === "save_resume_0.5") {
                                    saveResume(tabId, messages);
                                } else if (messages.status === "awake") {
                                    chrome.tabs.executeScript(null, {
                                        code: '$("html").html();'
                                    }, function (data) {
                                        // console.log(tabId);
                                        var res = startAwake(messages.Target, data.toString(), "CRM_SEARCH");
                                        console.log("上传成功 0.1 -> " + messages.ResumeId);
                                        if (res) {
                                            if (res.code === 200) {
                                                var i = 1;
                                                var _interval;
                                                var trackId = res.data;
                                                _interval = setInterval(function () {
                                                    i++;

                                                    if (i < RETRY) {
                                                        chrome.tabs.get(tabId, function () {
                                                            if (chrome.runtime.lastError) {
                                                                console.log("窗口已经被关闭了：" + chrome.runtime.lastError.message);
                                                                clearInterval(_interval);
                                                            }
                                                        });
                                                        var response = checkAwake(2, trackId);

                                                        if (response) {
                                                            if (response.code === 200) {
                                                                clearInterval(_interval);
                                                                doAwakeSuccess(tabId, response, messages, ".infr tbody");
                                                            } else if (response.code === 107){
                                                                clearInterval(_interval);
                                                                doAwakeSuccessFromLie100(tabId, response, messages, trackId, 'fiveone', ".infr tbody")
                                                            } else if (response.code === 100) {
                                                                clearInterval(_interval);
                                                                doAwakeFailed(tabId, messages, trackId, 'fiveone');

                                                            } else {
                                                                var cost = i * 5;
                                                                chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "' + cost + '秒过去啦...");'});
                                                            }
                                                        } else {
                                                            clearInterval(_interval);
                                                            chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "无法连接到唤醒服务器[pick]。请联系管理员！");'});
                                                        }
                                                    } else {
                                                        clearInterval(_interval);
                                                        chrome.tabs.executeScript(tabId, {
                                                            code: 'updateMessage("red", "啊呀，唤醒超时了！！！请稍后再试。");'
                                                        })
                                                    }
                                                }, 5000);
                                            } else if (res.code === 500) {
                                                chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "' + res.msg + '");'})
                                            } else {
                                                chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "唤醒服务器异常。code：！' + res.code + '");'});
                                            }
                                        } else {
                                            chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "无法连接到唤醒服务器[parse]。请联系管理员！");'});
                                        }
                                    });
                                } else if (messages.status === "start_download") {
                                    saveFlow(messages.trackId, "103", messages.Message, messages.userName, messages.ResumeId, messages.Target, messages.account, messages.mobile);
                                    console.log("开始下载 -> " + messages.ResumeId);

                                } else if (messages.status === "fail_download") {
                                    saveFlow(messages.trackId, "105", messages.Message, messages.userName, messages.ResumeId, messages.Target, messages.account, messages.mobile);
                                    console.log("下载失败 -> " + messages.ResumeId + " Message: " + messages.Message);
                                } else if (messages.status === "assigned") {
                                    assignedResume(tabId, messages);
                                }


                            } else if (messages.Target === "LIE_100") {
                                // lie100
                                if (messages.status === "awake") {
                                    var res = startLie100Awake(messages.userName, messages.ResumeId);
                                    console.log("上传成功 resumeId -> " + messages.ResumeId);
                                    if (res) {
                                        if (res.code === 200) {
                                            var i = 1;
                                            var _interval;
                                            var trackId = res.data;
                                            _interval = setInterval(function () {
                                                i++;

                                                if (i < RETRY) {
                                                    chrome.tabs.get(tabId, function () {
                                                        if (chrome.runtime.lastError) {
                                                            console.log("窗口已经被关闭了：" + chrome.runtime.lastError.message);
                                                            clearInterval(_interval);
                                                        }
                                                    });
                                                    var response = checkAwake(12, trackId);

                                                    if (response) {
                                                        if (response.code === 200) {
                                                            clearInterval(_interval);
                                                            doAwakeSuccess(tabId, response, messages, ".widget-box", 1)
                                                        } else if (response.code === 100) {
                                                            //唤醒失败
                                                            clearInterval(_interval);
                                                            doAwakeFailed(tabId, messages, trackId, 'lie100');

                                                        } else {
                                                            var cost = i * 5;
                                                            chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "' + cost + '秒过去啦...")'});
                                                        }
                                                    } else {
                                                        clearInterval(_interval);
                                                        chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "无法连接到唤醒服务器[pick]。请联系管理员！");'});
                                                    }
                                                } else {
                                                    clearInterval(_interval);
                                                    chrome.tabs.executeScript(tabId, {
                                                        code: 'updateMessage("red", "啊呀，唤醒超时了！！！请稍后再试。");'
                                                    })
                                                }
                                            }, 5000);
                                        } else if (res.code === 500) {
                                            chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "' + res.msg + '");'})
                                        } else {
                                            chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "唤醒服务器异常。code：！' + res.code + '");'});
                                        }
                                    } else {
                                        chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "无法连接到唤醒服务器[parse]。请联系管理员！");'});
                                    }
                                } else if (messages.status === "start_download") {

                                    saveFlow(messages.trackId, "103", messages.Message, messages.userName, messages.ResumeId, messages.Target, messages.account, messages.mobile);
                                    console.log("开始下载 -> " + messages.ResumeId);
                                    var response = downloadLie100Resume(messages.userName, messages.ResumeId, "CRM_BUY");
                                    if (response.code === 200) {
                                        var data = JSON.parse(response.data);
                                        console.log("下载成功 ->" + messages.ResumeId);
                                        saveFlow(messages.trackId, "104", "下载成功", messages.userName, messages.ResumeId, messages.Target, messages.account, data.mobile);
                                        chrome.tabs.executeScript(tabId, {code: 'updateMessage("green", "简历下载成功，请在页面查看联系方式。");$("#mf_action button").empty().css("background-color", "").removeAttr("id").off().html("不可用")'});
                                        chrome.tabs.executeScript(tabId, {code: 'var ak_mobile="' + data.mobile + '";var html = \'<span style="color:red;font-size:24px;">' + data.name + ' | ' + data.mobile + ' | ' + data.email + '</span>\';$(".widget-box").prepend(html);'});
                                    } else {
                                        saveFlow(messages.trackId, "105", "下载失败", messages.userName, messages.ResumeId, messages.Target, messages.account, messages.mobile);
                                        chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "下载失败，请重新尝试下载。");'});
                                        console.log("下载失败 ->" + messages.ResumeId)
                                    }
                                } else if (messages.status === "start_download_from_lie100") {

                                    saveFlow(messages.trackId, "103", messages.Message, messages.userName, messages.ResumeId, messages.Target, messages.account, messages.mobile, messages.distributeSource);
                                    console.log("开始下载 -> " + messages.ResumeId);
                                    var response = downloadLie100Resume(messages.userName, messages.ResumeId, "CRM_BUY");
                                    if (response.code === 200) {
                                        var data = JSON.parse(response.data);
                                        console.log("下载成功 ->" + messages.ResumeId);
                                        saveFlow(messages.trackId, "104", "下载成功", messages.userName, messages.ResumeId, messages.Target, messages.account, data.mobile, messages.distributeSource);
                                        chrome.tabs.executeScript(tabId, {code: 'updateMessage("green", "简历下载成功，请在页面查看联系方式。");$("#mf_action button").empty().css("background-color", "").removeAttr("id").off().html("不可用")'});
                                        if (messages.position) {
                                            chrome.tabs.executeScript(tabId, {code: 'var ak_mobile="' + data.mobile + '";var html = \'<br><span style="color:red;font-size:24px;">' + data.name + ' | ' + data.mobile + ' | ' + data.email + '</span>\';$("' + messages.callpath + '").prepend(html);'});
                                        } else {
                                            chrome.tabs.executeScript(tabId, {code: 'var ak_mobile="' + data.mobile + '";var html = \'<br><span style="color:red;font-size:24px;">' + data.name + ' | ' + data.mobile + ' | ' + data.email + '</span>\';$("' + messages.callpath + '").append(html);'});
                                        }
                                    } else {
                                        saveFlow(messages.trackId, "105", "下载失败", messages.userName, messages.ResumeId, messages.Target, messages.account, messages.mobile, messages.distributeSource);
                                        chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "下载失败（有本），你可以点击“下载简历”，直接从当前渠道购买。");'});
                                        chrome.tabs.executeScript(tabId, {file: 'js/'+messages.source+'/download.js'});
                                        console.log("下载失败 ->" + messages.ResumeId)
                                    }
                                } else if (messages.status === "assigned") {
                                    assignedResume(tabId, messages);
                                }


                            } else if (messages.Target === "LIE_PIN") {
                                // 猎聘
                                if (messages.status === "save_resume_0.5") {
                                    saveResume(tabId, messages);
                                } else if (messages.status === "awake") {
                                    chrome.tabs.executeScript(null, {
                                        code: '$("html").html();'
                                    }, function (data) {
                                        // console.log(tabId);
                                        var res = startAwake(messages.Target, data.toString(), "CRM_SEARCH", "", "", "", "", messages.name);
                                        console.log("上传成功 0.1 -> " + messages.ResumeId);
                                        if (res) {
                                            if (res.code === 200) {
                                                var i = 1;
                                                var _interval;
                                                var trackId = res.data;
                                                _interval = setInterval(function () {
                                                    i++;

                                                    if (i < RETRY) {
                                                        chrome.tabs.get(tabId, function () {
                                                            if (chrome.runtime.lastError) {
                                                                console.log("窗口已经被关闭了：" + chrome.runtime.lastError.message);
                                                                clearInterval(_interval);
                                                            }
                                                        });
                                                        var response = checkAwake(9, trackId);

                                                        if (response) {
                                                            if (response.code === 200) {
                                                                clearInterval(_interval);
                                                                doAwakeSuccess(tabId, response, messages, ".wrap.retop-wrap", 1)
                                                            } else if (response.code === 107) {
                                                                clearInterval(_interval);
                                                                doAwakeSuccessFromLie100(tabId, response, messages, trackId, 'liepin', ".wrap.retop-wrap", 1)
                                                            } else if (response.code === 100) {
                                                                clearInterval(_interval);
                                                                doAwakeFailed(tabId, messages, trackId, 'liepin');

                                                            } else {
                                                                var cost = i * 5;
                                                                chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "' + cost + '秒过去啦...");'});
                                                            }
                                                        } else {
                                                            clearInterval(_interval);
                                                            chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "无法连接到唤醒服务器[pick]。请联系管理员！");'});
                                                        }
                                                    } else {
                                                        clearInterval(_interval);
                                                        chrome.tabs.executeScript(tabId, {
                                                            code: 'updateMessage("red", "啊呀，唤醒超时了！！！请稍后再试。");'
                                                        })
                                                    }
                                                }, 5000);
                                            } else if (res.code === 500) {
                                                chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "' + res.msg + '");'})
                                            } else {
                                                chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "唤醒服务器异常。code：！' + res.code + '");'});
                                            }
                                        } else {
                                            chrome.tabs.executeScript(tabId, {code: 'updateMessage("red", "无法连接到唤醒服务器[parse]。请联系管理员！"});'});
                                        }
                                    });
                                } else if (messages.status === "start_download") {
                                    saveFlow(messages.trackId, "103", messages.Message, messages.userName, messages.ResumeId, messages.Target, messages.account, messages.mobile);
                                    console.log("开始下载 -> " + messages.ResumeId);

                                } else if (messages.status === "fail_download") {
                                    saveFlow(messages.trackId, "105", messages.Message, messages.userName, messages.ResumeId, messages.Target, messages.account, messages.mobile);
                                    console.log("下载失败 -> " + messages.ResumeId + " Message: " + messages.Message);
                                } else if (messages.status === "assigned") {
                                    assignedResume(tabId, messages);
                                }
                            }
                        }
                    }
                );
            }
            var url = tabs[0].url;
            // chrome.tabs.executeScript(null,{code:'alert(window.location.protocol+"\/\/"+window.location.host+window.location.pathname)'});
            if (url.indexOf("rd.zhaopin.com/resumepreview/resume/viewone/2/") >= 0 || url.indexOf("rd.zhaopin.com/resumepreview/resume/viewone/1/") >= 0
            || url.indexOf("ihr.zhaopin.com/resume/details/")>=0
            ) {
                // 智联下载逻辑
                // var target = "ZHI_LIAN";

                // 隐藏原有下载按钮，添加新的下载按钮
                chrome.tabs.executeScript(tabId, {code: 'var User=' + localStorage["ZHI_LIAN_ASSIGNED_USER"]});
                chrome.tabs.executeScript(tabId, {file: 'js/notice_tab.js'});
                chrome.tabs.executeScript(tabId, {file: 'js/zhilian/base.js'});


            } else if (url.indexOf("ehire.51job.com/Candidate/ResumeView.aspx") >= 0 || url.indexOf("ehire.51job.com/Candidate/ResumeViewFolder.aspx") >= 0) {
                // 前程下载逻辑
                // var source = "FIVE_ONE";
                chrome.tabs.executeScript(tabId, {code: 'var User=' + localStorage["FIVE_ONE_ASSIGNED_USER"]});
                chrome.tabs.executeScript(tabId, {file: 'js/notice_tab.js'});
                chrome.tabs.executeScript(tabId, {file: 'js/fiveone/base.js'});

            } else if (url.indexOf("resume.lie100.com/resume/detail.htm") >= 0) {
                // var target = "LIE_100";
                chrome.tabs.executeScript(tabId, {code: 'var User=' + localStorage["LIE_100_ASSIGNED_USER"]});
                chrome.tabs.executeScript(tabId, {file: 'js/notice_tab.js'});
                chrome.tabs.executeScript(tabId, {file: 'js/lie100/base.js'});

            } else if (url.indexOf("lpt.liepin.com/resume/showresumedetail") >= 0 || url.indexOf("h.liepin.com/resume/showresumedetail") >= 0) {

                chrome.tabs.executeScript(tabId, {code: 'var User=' + localStorage["LIE_PIN_ASSIGNED_USER"]});
                chrome.tabs.executeScript(tabId, {file: 'js/notice_tab.js'});
                chrome.tabs.executeScript(tabId, {file: 'js/liepin/base.js'});
            } else if (url.indexOf("https://www.baidu.com") === 0) {
                // var html = '<div class="navbar navbar-inverse' +
                //     ' navbar-fixed-bottom"><div class="navbar-inner"><!--fluid 是偏移一部分--><div class="container-fluid"><a class="brand" href="index.html"><img src="images/icons/Dribbble.png" /></a><font color="#5CB85C" style="font-size: larger">我是头或者底部</font><input type="text" style="margin-left: 700px;"/></div></div></div></div>';
                // chrome.tabs.executeScript(tabId, {code: '$(body).prepend(' + html + ')'})
            }
        });
    }
}
console.log("background");

chrome.tabs.onUpdated.addListener(function (tabId, info) {
    callback(tabId, info);
});
