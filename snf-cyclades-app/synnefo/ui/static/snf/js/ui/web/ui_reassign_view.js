// Copyright (C) 2010-2014 GRNET S.A.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.
// 

;(function(root){

    // root
    var root = root;
    
    // setup namepsaces
    var snf = root.synnefo = root.synnefo || {};
    var models = snf.models = snf.models || {}
    var storage = snf.storage = snf.storage || {};
    var ui = snf.ui = snf.ui || {};
    var util = snf.util = snf.util || {};

    var views = snf.views = snf.views || {}

    // shortcuts
    var bb = root.Backbone;

    views.ProjectSelectItemView = views.ext.SelectModelView.extend({
      tpl: '#project-select-model-tpl',

      select: function() {
        views.ProjectSelectItemView.__super__.select.call(this);
        this.model.trigger("change:_quotas");
      },
      
      deselect: function() {
        views.ProjectSelectItemView.__super__.deselect.call(this);
        this.model.trigger("change:_quotas");
      },

      set_current: function() {
        this._is_current = true;
        this.model.trigger('change:_project_is_current');
        $(this.el).addClass("current");
        this.set_enabled();
      },

      unset_current: function() {
        this._is_current = false;
        this.model.trigger('change:_project_is_current');
        $(this.el).removeClass("current");
      },

      is_current_str: function() {
        if (this._is_current) {
          return 'current'
        } else {
          return ''
        }
      },

      quotas_html: function() {
        var data = "<div>";
        var resolve = this.options.quotas_keys.length;
        var found = 0;
        _.each(this.options.quotas_keys, function(key) {
          var q = this.model.quotas.get(key);
          if (!q) { return }
          found += 1;
          
          var limit = q.get_readable("limit");
          var usage = q.get("usage");

          if (this.selected && !this._is_current) {
            var model_usage = this.parent_view.model_usage;
            var model = this.parent_view.resource_model;
            var usage_keys = model_usage.call(this.parent_view, model);
            var use = usage_keys[key];
            if (use) {
              usage = usage + use;
            }
          }

          if (!this.selected && this._is_current) {
            var model_usage = this.parent_view.model_usage;
            var model = this.parent_view.resource_model;
            var usage_keys = model_usage.call(this.parent_view, model);
            var use = usage_keys[key];
            if (use) {
              usage = usage - use;
              if (usage < 0) { usage = 0; }
            }
          }
          
          usage = q.get_readable("usage", false, usage);
          usage = "{0}/{1}".format(usage, limit);
          if (q.infinite()) {
              usage = "Unlimited";
          }
          var content = '<span class="resource-key">{0}:</span>';
          content += '<span class="resource-value">{1}</span>';
          data += content.format(q.get('resource').get('display_name'), 
                                 usage);
        }, this);
        if (found == 0) {
          data += "<p>No resources available</p>"
        }
        data += "</div>";
        return data;
      }
    });

    views.ProjectSelectView = views.ext.CollectionView.extend({
      initialize: function(options) {
        this.filter_func = options.filter_func || function(m) { return true }
        this.update_disabled = _.bind(this.update_disabled, this);
        views.ProjectSelectView.__super__.initialize.apply(this);
      },

      get_selected: function() {
        var selected = undefined;
        _.each(this._model_views, function(view, id){
          if (view.selected) { selected = view.model }
        });
        return selected;
      },
      
      post_remove_model_view: function(view) {
        view.unbind('click');
      },
      
      disabled_filter: function(model) {
        if (this.filter_func) {
            return !this.filter_func(model);
        }
        return false;
      },
      
      post_add_model_view: function(view, model) {
        this.update_disabled(view);
        view.bind('click', function() {
          if (view.disabled) { return }
          this.deselect_all();
        }, this);
      },
      
      _model_bindings: {},

      bind_custom_view_handlers: function(view, model) {
        var func
        model.quotas.bind('change', _.bind(function() {
          this.update_disabled(view)
        }, this));
      },
      
      unbind_custom_view_handlers: function(view, model) {
        model.quotas.unbind('change');
      },

      deselect_all: function(model) {
        this.collection.each(function(m) {
          var view = this._model_views[m.id];
          //if (view.disabled) { return }
          this._model_views[m.id].deselect();
        }, this);
      },

      set_selected: function(model) {
        this.deselect_all();
        if (this._model_views[model.id]) {
          this._model_views[model.id].select();
        }
      },

      set_current: function(model) {
        _.each(this._model_views, function(v) {
          v.unset_current();
        });
        if (this._model_views[model.id]) {
          this._model_views[model.id].set_current();
        }
      },

      model_view_options: function(model) {
        return {'quotas_keys': this.options.quotas_keys};
      },

      tpl: '#project-select-collection-tpl',
      model_view_cls: views.ProjectSelectItemView
    });
    
    views.ModelReassignView = views.Overlay.extend({
        title: "Reassign machine",
        overlay_id: "overlay-select-projects",
        content_selector: "#project-select-content",
        css_class: "overlay-info",
        can_fit_func: function(project) { 
          return project.quotas.can_fit(this.model_usage(this.model))
        },

        initialize: function(options) {
            views.ModelReassignView.__super__.initialize.apply(this);
            this.list = this.$(".projects-list ul");
            this.empty_message = this.$(".empty-message");
            this.submit_button = this.$(".form-action.submit");
            this.in_progress = false;
            this.init_handlers();
          
            this.$(".description").text(this.description || "");
            if (this.collection) { this.init_collection_view(this.collection) }
        },
        
        init_collection_view: function(collection) {
            if (this.collection_view) { this.collection_view.destroy() }
            this.collection_view = new views.ProjectSelectView({
              collection: collection,
              el: this.list,
              filter_func: _.bind(this.can_fit_func, this),
              quotas_keys: this.resources
            });

            this.collection_view.bind("change:select", function(item) {
                this.handle_project_change(item.model);
            }, this);

            this.collection_view.show(true);
            this.collection_view.model_usage = this.model_usage;
            this.collection_view.resource_model = this.model;
            var project = this.model.get('project');
            if (project && !(project.get('missing') && !project.get('resolved'))) {
              this.collection_view.set_current(this.model.get('project'));
              this.collection_view.set_selected(this.model.get('project'));
            }
            this.list.append($(this.collection_view.el));
            this.handle_project_change();
        },

        handle_project_change: function(project) {
            var project = project || this.collection_view.get_selected();
            if (project.id == this.model.get('project').id) {
                this.submit_button.addClass("disabled");
            } else {
                this.submit_button.removeClass("disabled");
            }
        },

        init_handlers: function() {
          this.submit_button.bind('click', _.bind(this.submit, this));
        },

        submit: function() {
          if (this.submit_button.hasClass("disabled")) { return }
          if (this.in_progress) { return }
          var project = this.collection_view.get_selected();
          if (project.id == this.model.get('project').id) {
            this.hide();
          }
          var complete = _.bind(function() {
            this.submit_button.removeClass("in-progress");
            this.in_progress = false;
            synnefo.storage.projects.delay_fetch(2000);
            this.hide();
          }, this);
          this.assign_to_project(this.model, project, complete, complete);
          this.submit_button.addClass("in-progress");
          this.in_progress = true;
        },
        
        update_model_details: function() {
          this.set_subtitle(this.model.get('name'));
        },

        show: function(model) {
          this.model = model;
          this.init_collection_view(synnefo.storage.projects);
          views.ModelReassignView.__super__.show.call(this);
          this.update_model_details();
        },

        onClose: function() {
          if (this.collection_view) {
            this.collection_view.destroy();
          }
          delete this.collection_view;
        }
    });

    views.VmReassignView = views.ModelReassignView.extend({
      title: 'Set machine project',
      description: 'Select project assign machine to',
      resources: ['cyclades.vm', 'cyclades.ram', 
                  'cyclades.cpu', 'cyclades.disk'],

      model_usage: function(model) {
          var quotas = model.get_flavor().quotas();
          var total = false;
          if (model.get("status") == "STOPPED") {
            total = true;
          }
          return quotas;
      },

      can_fit_func: function(project) {
          var quotas = this.model.get_flavor().quotas();
          var total = false;
          if (this.model.get("status") == "STOPPED") {
            total = true;
          }
          return project.quotas.can_fit(quotas, total);
      },
      
      update_model_details: function() {
          var name = _.escape(synnefo.util.truncate(this.model.get("name"), 70));
          this.set_subtitle(name + snf.ui.helpers.vm_icon_tag(this.model, "small"));

          var el = $("<div></div>");
          var cont = $(this.el).find(".model-usage");
          cont.empty().append(el);
          
          var flavor = this.model.get_flavor();
          _.each(['ram', 'disk', 'cpu'], function(key) {
            var res = synnefo.storage.resources.get('cyclades.' + key)
            el.append($('<span class="key">' + res.get('display_name') + 
                        ':</span>'));
            el.append($('<span class="value">' + 
                        flavor.get_readable(key) + '</span>'));
          });
      },

      assign_to_project: function(model, project, complete, fail) {
        model.call("reassign", complete, fail, {project_id: project.id});
      }
    });

    views.IPReassignView = views.ModelReassignView.extend({
      title: 'Set IP address project',
      description: 'Select project to assign IP address to',
      resources: ['cyclades.floating_ip'],
      model_usage: function() { return {'cyclades.floating_ip': 1}},
      assign_to_project: function(model, project, complete, fail) {
        this.model.reassign_to_project(project, complete, complete);
      }
    });

    views.NetworkReassignView = views.ModelReassignView.extend({
      title: 'Set private network project',
      resources: ['cyclades.network.private'],
      description: 'Select project to assign private network to',
      model_usage: function() { return {'cyclades.network.private': 1}},
      assign_to_project: function(model, project, complete, fail) {
        this.model.reassign_to_project(project, complete, complete);
      }
    });

    views.VolumeReassignView = views.ModelReassignView.extend({
      title: 'Set disk project',
      resources: ['cyclades.disk'],
      description: 'Select project to assign disk to',
      model_usage: function(model) { 
          return {'cyclades.disk': model.get('size') * Math.pow(1024, 3)}
      },
      assign_to_project: function(model, project, complete, fail) {
        this.model.reassign_to_project(project, complete, complete);
      }
    });
})(this);
