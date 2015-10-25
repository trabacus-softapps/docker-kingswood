openerp.kingswood = function(openerp) {
  openerp.web.form.widgets.add('upper_case', 'openerp.kingswood.upper_case');
  openerp.kingswood.upper_case = openerp.web.form.FieldChar.extend({
    template: 'upper_case',
    
       
       init: function (view, code) {
            this._super(view, code);
            console.log('loading...');
        },
       
       start:function(){
        this._super.apply(this, arguments);
        	var self = this;
       },
       
       
    
    initialize_content: function() {
        this._super();
        var self = this;
        
        $('input').on('keyup', function(event) {
     		self.$el.find('input').val(self.$el.find('input').val().toUpperCase());
        });
        
    },
  
  });
 
}
    
    
    
    