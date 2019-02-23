(function () {

  $('#viewSecret').click(function () {
    var form = $('<form/>')
      .attr('id', 'viewSecretForm')
      .attr('method', 'post');
    form.appendTo($('body'));
    form.submit();
  });
})();