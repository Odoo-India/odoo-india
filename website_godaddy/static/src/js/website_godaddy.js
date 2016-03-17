odoo.define('website_godaddy.website_godaddy', function (require) {

var ajax = require('web.ajax');
var core = require('web.core');


var QWeb = core.qweb;

var API_KEY = 'UzkawtNd_U87Q2U8qmSrEbGcdEsfqEt';
var SECRET_KEY = 'GaSBQXG5oXV3Pzbgbx75xp';

var DOMAINS = {};

var loaded_domains = false;

var AVAILABLE_DOMAIN = false;

var is_valid_domain = false;

var contact_details = {
    "nameFirst": "jams",
    "nameMiddle": "jacky",
    "nameLast": "jerry",
    "organization": "odoo",
    "jobTitle": "developer",
    "email": "dka@odoo.com",
    "phone": "+1.4805058800",
    "fax": "+1.4805058800",
    "addressMailing": {
        "address1": "plot-no 25, sector-26",
        "address2": "plot-no 25, sector-26",
        "city": "Gandhinagar",
        "state": "Gujarat",
        "postalCode": "382007",
        "country": "IN"
    } 
}
/*this is sample schema value for testing*/
var SAMPLE = {
    "domain": "opendays.buzz",
    "consent": {
    "agreementKeys": [
        "DNRA"
    ],
        "agreedBy": "180.211.100.3",
        "agreedAt": "2015-10-28T11:34:51Z"
    },
    "nameServers":["odoo.com"],
    "contactRegistrant": contact_details,
    "contactAdmin": contact_details,
    "contactTech": contact_details,
    "contactBilling": contact_details
}


$(document).ready(function () {

    var $form = $('#godaddy_form');
    setup_request();

    $form.on("click", 'button[type="submit"]', function (ev) {
        var domain = $form.find('#domain').val();
        //check fo valid domain
        if (domain.indexOf('.') >= 1) {
            is_valid_domain = true;
        } else {
            is_valid_domain = false;
        }

        var url = "https://api.ote-godaddy.com/v1/domains/suggest?query=";
        var furl = url.concat(domain);

        var aurl = "https://api.ote-godaddy.com/v1/domains/available?domain=";
        var afurl = aurl.concat(domain);

        send_request(furl, afurl);

        //check if domain list is already exist then remove it...
        var all_raw = $('#response table .no_result');
        if (all_raw.length) {
            $(all_raw).nextAll().remove();
        }
        return false;

    });

    function bind_events() {
        $('#response .search_domain').on('click', function() {
            var list_tld = $('#response input[type="checkbox"]:checked').map(function() {return this.value;}).get().join(',').split(",")
            var all_domains = []
            _.each(DOMAINS, function(domain){
                var tld = domain['domain'].substr(domain['domain'].indexOf(".") + 1);
                if (_.contains(list_tld, tld)) {
                    all_domains.push(domain['domain'])
                }
            });
            set_suggested_domain(all_domains);
        });
        $('#response table button').on('click', function(ev){
            var $purchase_domain = $(ev.currentTarget);
            //retrive the schema to be submitted when registering a Domain
            // for specified TLDs
            $.ajax({
                type: 'POST',
                data: SAMPLE,
                url: "https://api.ote-godaddy.com/v1/domains/purchase/validate",
                beforeSend: function() {
                    $purchase_domain.after("<strong class='pull-right validator-img'>Vaidating schema <img src='/website_godaddy/static/src/img/throbber.gif'/></strong");
                    $purchase_domain.hide();
                },
                success: function(data) {
                    $('#response table .validator-img').hide();
                    $purchase_domain.after('<div class="pull-right"><h4><strong><span class="fa fa-check text-success">  SELECTED</strong></h4><span class="pull-right fa fa-times"><span class="small"> Remove<span/></div>');
                },
                error: function(error) {
                    $('#response table .validator-img').hide();
                    $purchase_domain.remove();
                    show_error(error);
                },
            }).then(function(){
                $.ajax({
                    type: 'POST',
                    url: "https://api.ote-godaddy.com/v1/domains/purchase",
                    data: SAMPLE,
                    success: function(data) {
                        console.log('Success Fully Purchased',data);
                    },
                    error: function(error) {
                        show_error(error);
                    },
                })
            })
        });

    }
    function load_slider() {
        var all_domains = [];
        $("#slider-range").slider({
            range: true,
            min: 1,
            max: 30,
            values: [ 1, 10 ],
              slide: function( event, ui ) {
                var all_domains = []
                _.each(DOMAINS, function(domain){
                    if (domain['domain'].length >= ui.values[0] && domain['domain'].length <= ui.values[1]) {
                        all_domains.push(domain['domain'])
                    }
                });
                $( "#amount" ).val( "" + ui.values[ 0 ] + " - " + ui.values[ 1 ] );
                set_suggested_domain(all_domains);
              }
        });
    }
    function set_suggested_domain(all_domains) {
        var str = "";
        var all_raw = $('#response .table button');
        $('#response .table .no_result').hide();
        if (all_raw.length && all_domains.length) {
           _.each(all_raw, function(raw) {
                if (_.contains(all_domains, $(raw).attr('id'))) {
                    $(raw).parent().parent().show();
                } else {
                    $(raw).parent().parent().hide();
                }
           });
        } else {
            if (all_domains.length) {
                str = "";
                _.each(all_domains, function (domain) {
                    str += "<tr>";
                    str += "<td>" + domain + "<button id="+ domain +" href='#' class='pull-right btn btn-sm btn-success'>Buy</button></td>"
                    str += "</tr>"
                });
                $('#response .table').append(str);
            } else {
                $('#response .table tr').hide();
                $('#response .table .no_result').removeClass('hide').show();
            }
        }
    }
    function set_tlds(domains) {
        var str = "";
        _.each(domains, function (domain) {
            str += "<li>";
            str += "<input type='checkbox' value='" + domain['name'] + "' name='" + domain['name'] + "'> <span class='ml8'>" + domain['name'] + '</span></input>'
            str += "</li>"
        });
        $('#response .list_tld').html(str);
    }
    function setup_request() {
        $.ajaxSetup({
            type: "GET",
            headers: {
                'Authorization': 'sso-key '+API_KEY+':'+SECRET_KEY+'',
                'Accept': 'application/json',
            },
        });
    }
    function send_request(furl, afurl) {
        var suggest_domain = $.ajax({
            url: furl,
            beforeSend: function() {
                $form.find("#loader_image").removeClass('hide').show();
            },
            success: function(data) { 
                DOMAINS = data
                loaded_domains = true;
                var all_domains = [];
                _.each(data, function (domain) {
                    all_domains.push(domain['domain']);
                });
                set_suggested_domain(all_domains);
            },
        });
        var tlds_domain = $.ajax({
            url: "https://api.ote-godaddy.com/v1/domains/tlds",
            success: function(data) {
                set_tlds(data);
            },
        });
        if (is_valid_domain) {
            var available_domain = $.ajax({
                url: afurl,
                success: function(data) {
                    AVAILABLE_DOMAIN = data;
                },
            });
        } else {
            var available_domain = undefined;
        }
        handle_request(suggest_domain, tlds_domain, available_domain);
    }

    //handle a multiple request in one go!!
    function handle_request(suggest_domain, tlds_domain, available_domain) {
        $.when(suggest_domain, tlds_domain, available_domain).then(
            function(sucess) {
                setup_dom();
            },
            function(error) {
                $form.find("#loader_image").hide();
                show_error(error);
            }
        );
    }
    function setup_dom() {
        $form.find("#loader_image").hide();
        bind_events();
        load_slider();
        if (AVAILABLE_DOMAIN && AVAILABLE_DOMAIN['available']) {
            $('#response .check_availability .available').removeClass('hide').show();
            $('#response .check_availability .unavailable').hide();
            $('#response .check_availability').removeClass('hide').show();
        } else if (AVAILABLE_DOMAIN && !AVAILABLE_DOMAIN['available']) {
            $('#response .check_availability .unavailable').removeClass('hide').show();
            $('#response .check_availability .available').hide();
            $('#response .check_availability').removeClass('hide').show();
        } else {
            $('#response .check_availability').removeClass('show').hide();
        }
        $('#response .domain').text(AVAILABLE_DOMAIN['domain']);
        $('#response .currency').text(AVAILABLE_DOMAIN['currency']);
        $('#response .period').text(AVAILABLE_DOMAIN['period']);
        $('#response .price').text(AVAILABLE_DOMAIN['price']);
        $('#response').removeClass('hide').show();
        $('#tld').removeClass('hide').show();
        AVAILABLE_DOMAIN = false;
    }
    function show_error(error) {
        if (error && error['responseText']) {
            var error = jQuery.parseJSON(error['responseText']);
            $form.find(".error-details .error-code").text(error.code);
            $form.find(".error-details .error-message").text(error.message);
        } else {
            $form.find(".error-details .error-message").text("Please Check Your Internet Connection");
        }
        $form.find(".api-error").removeClass('hide').show();
    }

});


});
