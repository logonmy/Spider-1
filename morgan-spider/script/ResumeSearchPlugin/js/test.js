var crm_resumeId = "42968";
$("#mloading").hide();
swal({
    title: "恭喜您",
    html: "该简历尚未被分配，是否分配到你(刘小东)的名下？",
    type: "question",
    showCancelButton: true,
    confirmButtonText: "继续",
    cancelButtonText: "取消",
    reverseButtons: true
}).then(function () {
    chrome.runtime.sendMessage({
        "Target": "ZHI_LIAN",
        "status": "assigned",
        "Message": crm_resumeId
    })
});