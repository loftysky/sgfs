import os
import fnmatch

import yaml

from . import utils


def _get_or_eval(entities, config, name, default=None):
    for namespace in (config, entities):
        if name in namespace:
            return namespace[name]
        expr_name = name + '_expr'
        if expr_name in namespace:
            return utils.eval_expr_or_func(namespace[expr_name], entities, config)
    return default


class Structure(object):
    
    @classmethod
    def from_config(cls, entities, config, default_type=None):
        
        type_ = config.get('type', default_type)
        
        constructor = {
            'directory': Directory,
            'entity': Entity,
            'include': Include,
            'file': File,
        }.get(type_)
        
        if not constructor:
            raise ValueError('could not determine type')
        
        if constructor._should_construct(entities, config):
            return constructor(entities, config)
        
    @classmethod
    def _should_construct(cls, entities, config):
        if 'condition' not in config:
            return True
        return bool(utils.eval_expr_or_func(config['condition'], entities, config))
    
    def __init__(self, entities, config, children=None):
        
        self.children = children or []
        
        self.name = str(_get_or_eval(entities, config, 'name', ''))
        self.file = config.get('__file__')
    
    def _repr_headline(self):
        return '%s %r at 0x%x from %r' % (
            self.__class__.__name__,
            self.name,
            id(self),
            self.file,
        )
    
    def pprint(self, depth=0):
        print '\t' * depth + self._repr_headline()
        for child in sorted(self.children, key=lambda x: x.name):
            child.pprint(depth + 1)
    


class Directory(Structure):
    
    def __init__(self, entities, config, *args, **kwargs):
        super(Directory, self).__init__(entities, config, *args, **kwargs)
        
        template = config.get('template')
        if template:
            
            # Build up the ignore list.
            ignore = ['._*', '.sgfs-ignore']
            ignore_file = os.path.join(template, '.sgfs-ignore')
            if os.path.exists(ignore_file):
                for line in open(ignore_file):
                    line = line.strip()
                    if not line or line[0] == '#':
                        continue
                    ignore.append(ignore_file)
            
            # List the directory and apply the ignore list.
            names = os.listdir(template)
            names = [x for x in names if not any(fnmatch.fnmatch(x, pattern) for pattern in ignore)]
            paths = [os.path.join(template, name) for name in names]
            
            # Find anything special, and turn it into children.
            for special in [x for x in paths if x.endswith('.yml')]:
                
                config = yaml.load(open(special).read()) or {}
                config['__file__'] = special
                local_template = os.path.splitext(special)[0]
                
                if os.path.exists(local_template):
                    config['template'] = local_template
                    paths.remove(local_template)
                
                child = Structure.from_config(entities, config, default_type='directory')
                if child is not None:
                    self.children.append(child)
        
            # Generic files/directories.
            for path in [x for x in paths if not x.endswith('.yml')]:
                default_type = 'directory' if os.path.isdir(path) else 'file'
                self.children.append(Structure.from_config(
                    entities,
                    {
                        'name': os.path.basename(path),
                        'template': path
                    },
                    default_type=default_type,
                ))
    
    def _repr_headline(self):
        return (self.name or '.') + '/'
                    


class Entity(Directory):
    
    def __init__(self, entities, config, *args, **kwargs):
        super(Entity, self).__init__(entities, config, *args, **kwargs)
        self.entity = entities['self']
    
    def _repr_headline(self):
        return '%s/ <- %s %s' % (self.name or '.', self.entity['type'], self.entity['id']) 
    


class Include(Directory):
    
    def _repr_headline(self):
        return '<%s %s>' % (self.__class__.__name__, self.file)


class File(Structure):
    
    def _repr_headline(self):
        return self.name
    

