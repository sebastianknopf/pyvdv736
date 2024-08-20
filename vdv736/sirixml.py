def exists(obj, path):
    path = path.split('.')
    
    level0 = path[0]
    level1 = '.'.join(path[1:])
    
    return obj is not None and hasattr(obj, level0) if len(path) == 1 else exists(getattr(obj, level0), level1) if hasattr(obj, level0) else False

def get_elements(obj, path):
    if exists(obj, path):
        path = path.split('.')
        
        destination = obj
        for element in path:
            destination = getattr(destination, element)
            
        return destination

    return list()
    
def get_value(obj, path, default=None):
    if exists(obj, path):
        path = path.split('.')
        
        destination = obj
        for element in path:
            destination = getattr(destination, element)
            
        if hasattr(destination, 'text'):
            return destination.text
        else:
            return default
        
    return default

def get_attribute(obj, path, default=None):
    objectpath = path.split('.')
    objectpath = '.'.join(objectpath[:-1])
    
    if exists(obj, objectpath):
        path = path.split('.')
        
        destination = obj
        for element in path[:-1]:
            destination = getattr(destination, element)
            
        if hasattr(destination, 'attr') and path[-1] in destination.attr:
            return destination.get(path[-1])
        else:
            return default
            
    return default