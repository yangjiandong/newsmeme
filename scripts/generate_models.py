#-*- coding: utf-8 -*-
#使用SqlAutocode，根据数据库已有表，产生符合Flask-SqlAlchemy要求的models的定义

import os.path
from flask import Flask
from sqlautocode import config
from sqlautocode.declarative import *
from sqlautocode.formatter import _repr_coltype_as
from flask.ext.sqlalchemy import SQLAlchemy

singular = plural = lambda x: x
constants.COLUMN = 'db.' + constants.COLUMN
constants.HEADER_DECL = """from sqlalchemy import *
if __name__ == '__main__':
    from flask import Flask
    from flask.ext.sqlalchemy import SQLAlchemy

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = '%s'
    db = SQLAlchemy(app)
else:
    from .db import db


"""


def no_prefix_wrapper(f, prefix=None):
    def _name2label(name, schema=None):
        if schema:
            if name.startswith(schema+'.'):
                name = '.'.join(name.split('.')[1:])
        if prefix and name.startswith(prefix):
            name = name[ len(prefix):]
        label = str(''.join([s.capitalize() for s in
                   re.findall(r'([A-Z][a-z0-9]+|[a-z0-9]+|[A-Z0-9]+)', name)]))
        return label
    return _name2label


def column_repr(self):

    kwarg = []
    if self.key != self.name:
        kwarg.append( 'key')

    if hasattr(self, 'primary_key') and self.primary_key:
        self.primary_key = True
        kwarg.append( 'primary_key')

    if not self.nullable:
        kwarg.append( 'nullable')
    if self.onupdate:
        kwarg.append( 'onupdate')
    if self.default:
        kwarg.append( 'default')
    ks = ', '.join('%s=%r' % (k, getattr(self, k)) for k in kwarg)
    if self.server_default:
        ks += ', ' if ks else ''
        ks += ('default=%s' % self.server_default.arg.text)

    name = self.name

    if not hasattr(config, 'options') and self.config.options.generictypes:
        coltype = repr(self.type)
    elif type(self.type).__module__ == 'sqlalchemy.types':
        coltype = repr(self.type)
    else:
        # Try to 'cast' this column type to a cross-platform type
        # from sqlalchemy.types, dropping any database-specific type
        # arguments.
        for base in type(self.type).__mro__:
            if (base.__module__ == 'sqlalchemy.types' and
                base.__name__ in sqlalchemy.__all__):
                coltype = _repr_coltype_as(self.type, base)
                break
        # FIXME: if a dialect has a non-standard type that does not
        # derive from an ANSI type, there's no choice but to ignore
        # generic-types and output the exact type. However, import
        # headers have already been output and lack the required
        # dialect import.
        else:
            coltype = repr(self.type)

    data = {'name': self.name,
            'type': coltype,
            'constraints': ', '.join(["ForeignKey('%s')"%cn.target_fullname for cn in self.foreign_keys]),
            'args': ks and ks or '',
            }

    if data['constraints']:
        if data['constraints']: data['constraints'] = ', ' + data['constraints']
    if data['args']:
        if data['args']: data['args'] = ', ' + data['args']

    return constants.COLUMN % data


class FlaskModelFactory(ModelFactory):

    def __init__(self, name, conn):
        self.name = name
        argv = ['sqlautocode', conn, '-d', '-g', '-i']
        config.configure(argv)
        config.interactive, config.schema, config.example = None, None, False
        super(FlaskModelFactory, self).__init__(config)

    def _table_repr(self, table):
        s = "db.Table(u'%s',\n"%(table.name)
        for column in table.c:
            s += "    %s,\n"%column_repr(column)
        if self.name != "default":
            s +="    info={'bind_key': '%s'}\n"%self.name
        #if table.schema:
        #    s +="    schema='%s'\n"%table.schema
        s+=")"
        return s

    def create_model(self, table):
        #partially borrowed from Jorge Vargas' code
        #http://dpaste.org/V6YS/
        log.debug('Creating Model from table: %s'%table.name)

        model_name = self.find_new_name(singular(name2label(table.name)), self.used_model_names)
        self.used_model_names.append(model_name)
        is_many_to_many_table = self.is_many_to_many_table(table)
        table_name = self.find_new_name(table.name, self.used_table_names)
        self.used_table_names.append(table_name)

        mtl = self.model_table_lookup


        class Temporal(self.DeclarativeBase):
            __table__ = table

            @classmethod
            def _relation_repr(cls, rel):
                target = rel.argument
                if target and inspect.isfunction(target):
                    target = target()
                if isinstance(target, Mapper):
                    target = target.class_
                target = target.__name__
                primaryjoin=''
                lookup = mtl()
                if rel.primaryjoin is not None and hasattr(rel.primaryjoin, 'right'):
                    right_lookup = lookup.get(rel.primaryjoin.right.table.name, '%s.c'%rel.primaryjoin.right.table.name)
                    left_lookup = lookup.get(rel.primaryjoin.left.table.name, '%s.c'%rel.primaryjoin.left.table.name)

                    primaryjoin = ", primaryjoin='%s.%s==%s.%s'"%(left_lookup,
                                                                  rel.primaryjoin.left.name,
                                                                  right_lookup,
                                                                  rel.primaryjoin.right.name)
                elif hasattr(rel, '_as_string'):
                    primaryjoin=', primaryjoin="%s"'%rel._as_string

                secondary = ''
                secondaryjoin = ''
                if rel.secondary is not None:
                    secondary = ", secondary=%s"%rel.secondary.name
                    right_lookup = lookup.get(rel.secondaryjoin.right.table.name, '%s.c'%rel.secondaryjoin.right.table.name)
                    left_lookup = lookup.get(rel.secondaryjoin.left.table.name, '%s.c'%rel.secondaryjoin.left.table.name)
                    secondaryjoin = ", secondaryjoin='%s.%s==%s.%s'"%(left_lookup,
                                                                  rel.secondaryjoin.left.name,
                                                                  right_lookup,
                                                                  rel.secondaryjoin.right.name)
                backref=''
#                if rel.backref:
#                    backref=", backref='%s'"%rel.backref.key
                return "%s = relation('%s'%s%s%s%s)"%(rel.key, target, primaryjoin, secondary, secondaryjoin, backref)

            @classmethod
            def __repr__(cls):
                try:
                    mapper = None
                    try:
                        mapper = class_mapper(cls)
                    except exc.InvalidRequestError:
                        log.warn("A proper mapper could not be generated for the class %s, no relations will be created"%model_name)
                    s = ""
                    s += "class "+model_name+'(db.Model):\n'
                    if cls.__bind_key__ != "default":
                        s += "    __bind_key__ = '%s'\n"%cls.__bind_key__
                    if is_many_to_many_table:
                        s += "    __table__ = %s\n\n"%table_name
                    else:
                        s += "    __tablename__ = '%s'\n"%table_name
                        if hasattr(cls, '__table_args__'):
                            #if cls.__table_args__[0]:
                                #for fkc in cls.__table_args__[0]:
                                #    fkc.__class__.__repr__ = foreignkeyconstraint_repr
                                #    break
                            s+="    __table_args__ = %s\n"%cls.__table_args__
                        s+="\n"
                        for column in cls.__table__.c:
                            s += "    %s = %s\n"%(column.name, column_repr(column))
                    ess = s
                    # this is only required in SA 0.5
                    if mapper and RelationProperty:
                        for prop in mapper.iterate_properties:
                            if isinstance(prop, RelationshipProperty):
                                s+='    %s\n'%cls._relation_repr(prop)
                    return s

                except Exception, e:
                    log.error("Could not generate class for: %s"%cls.__name__)
                    from traceback import format_exc
                    log.error(format_exc())
                    return ''


        #hack the class to have the right classname
        Temporal.__name__ = model_name

        #set up some blank table args
        Temporal.__table_args__ = {}

        #add in the schema
        Temporal.__bind_key__ = self.name
        #if self.config.schema:
        #    Temporal.__table_args__[1]['schema'] = table.schema

        #trick sa's model registry to think the model is the correct name
        if model_name != 'Temporal':
            Temporal._decl_class_registry[model_name] = Temporal._decl_class_registry['Temporal']
            del Temporal._decl_class_registry['Temporal']

        #add in single relations
        fks = self.get_single_foreign_keys_by_column(table)
        for column, fk in fks.iteritems():
            related_table = fk.column.table
            if related_table not in self.tables:
                continue

            log.info('    Adding <primary> foreign key for:%s'%related_table.name)
            backref_name = plural(table_name)
            rel = relation(singular(name2label(related_table.name, related_table.schema)),
                           primaryjoin=column==fk.column)#, backref=backref_name)

            setattr(Temporal, related_table.name, _deferred_relationship(Temporal, rel))

        #add in the relations for the composites
        for constraint in table.constraints:
            if isinstance(constraint, ForeignKeyConstraint):
                if len(constraint.elements) >1:
                    related_table = constraint.elements[0].column.table
                    related_classname = singular(name2label(related_table.name, related_table.schema))

                    primary_join = "and_(%s)"%', '.join(["%s.%s==%s.%s"%(model_name,
                                                                        k.parent.name,
                                                                        related_classname,
                                                                        k.column.name)
                                                      for k in constraint.elements])
                    rel = relation(related_classname,
                                    primaryjoin=primary_join
                                    #foreign_keys=[k.parent for k in constraint.elements]
                               )

                    rel._as_string = primary_join
                    setattr(Temporal, related_table.name, rel) # _deferred_relationship(Temporal, rel))


        #add in many-to-many relations
        for join_table in self.get_related_many_to_many_tables(table.name):

            if join_table not in self.tables:
                continue
            primary_column = [c for c in join_table.columns if c.foreign_keys and list(c.foreign_keys)[0].column.table==table][0]

            for column in join_table.columns:
                if column.foreign_keys:
                    key = list(column.foreign_keys)[0]
                    if key.column.table is not table:
                        related_column = related_table = list(column.foreign_keys)[0].column
                        related_table = related_column.table
                        if related_table not in self.tables:
                            continue
                        log.info('    Adding <secondary> foreign key(%s) for:%s'%(key, related_table.name))
                        setattr(Temporal, plural(related_table.name), _deferred_relationship(Temporal,
                                 relation(singular(name2label(related_table.name,
                                                     related_table.schema)),
                                          secondary=join_table,
                                          primaryjoin=list(primary_column.foreign_keys)[0].column==primary_column,
                                          secondaryjoin=column==related_column
                                          )))
                        break;

        return Temporal


def gen_models_dir(app, models_dir):
    #找到并建立models文件夹和__init__.py文件
    if not models_dir:
        app_root = app.config.get('APPLICATION_ROOT', '')
        if not app_root:
            app_root = os.path.dirname( os.path.dirname( os.path.realpath(__file__) ) )
        models_dir = os.path.join(app_root, 'models')
    if not os.path.exists(models_dir):
        os.mkdir(models_dir)
    init_file = os.path.join(models_dir, '__init__.py')
    with open(init_file, 'wb') as fh:
        fh.write('#-*- coding: utf-8 -*-\n')
    return models_dir


def write_db_file(db_file):
    #建立数据库定义文件
    with open(db_file, 'wb') as fh:
        fh.write('#-*- coding: utf-8 -*-\n')
        fh.write('\n')
        fh.write('from flask.ext.sqlalchemy import SQLAlchemy\n')
        fh.write('\n\n')
        fh.write('db = SQLAlchemy()\n')


def write_schema_file(factory, schema_file, name='default'):
    #建立数据库定义文件
    with open(schema_file, 'wb') as fh:
        fh.write("#-*- coding: utf-8 -*-\n")
        fh.write('\n')
        fh.write( repr(factory) )
        fh.write('\n')
        fh.write("if __name__ == '__main__':\n")
        if name == 'default':
            fh.write("    db.create_all(bind=None)\n")
        else:
            fh.write("    db.create_all(bind=['%s'])\n" % name)


def generate_models(app, models_dir=None):
    db = SQLAlchemy(app)
    conns = {
        'default': app.config.get('SQLALCHEMY_DATABASE_URI') or {},
    }
    conns.update( app.config.get('SQLALCHEMY_BINDS') or {} )

    models_dir = gen_models_dir(app, models_dir)
    db_file = os.path.join(models_dir, 'db.py')
    if not os.path.exists(db_file):
        write_db_file(db_file)
    for name, conn in conns.items():
        if not conn:
            continue
        schema_file = os.path.join(models_dir, '%s.py' % name)
        if not os.path.exists(schema_file):
            factory = FlaskModelFactory(name, conn)
            write_schema_file(factory, schema_file, name)


if __name__ == '__main__':
    import sys
    sys.path.append(
        os.path.dirname( os.path.dirname( os.path.realpath(__file__) ) )
    )
    app = Flask(__name__)
    app.config.from_object('settings')
    name2label = no_prefix_wrapper(name2label, app.config.get('TABLE_PREFIX'))
    generate_models(app)
