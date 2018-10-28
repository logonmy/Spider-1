/**
 * Created by wuyue on 17-8-9.
 */

if (User !== undefined) {
    $("body").prepend('<div class="box box-3"><dl><dd>全网简历搜索插件<b id="small_button"' +
        ' class="up"></b></dd><ul><li><span>当前用户：</span><i id="mf_user">' + User.userName + '</i></li> <li><span>系统消息：</span><i id="mf_message" >欢迎使用全网简历搜索插件</i></li> <div id="lengthcheck"></div><li id="mf_action"><span>可执行操作：</span><button>不可用</button></li></ul></dl></div>');

    $(function () {
        $('.box-3 dl').each(function () {
            $(this).dragging({
                move: 'both',
                randomPosition: false,
                hander: 'dd'
            });
        });
    });
}

function updateMessage(color, message) {
    $("#mf_action").css("margin-top", "");
    $("#mf_message").empty().css('color', color).html(message);
    var word = $("#mf_message").html();
    if (word.replace(/[\u0391-\uFFE5]/g,"aa").length > 30) {
        $("#mf_action").css("margin-top", "36px");
    }
}
