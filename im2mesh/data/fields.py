import os
import glob
import random
from PIL import Image
import numpy as np
import trimesh
from im2mesh.data.core import Field
from im2mesh.utils import binvox_rw


class IndexField(Field):
    ''' Basic index field.'''
    def load(self, model_path, idx, category):
        ''' Loads the index field.

        Args:
            model_path (str): path to model
            idx (int): ID of data point
            category (int): index of category
        '''
        return idx

    def check_complete(self, files):
        ''' Check if field is complete.
        
        Args:
            files: files
        '''
        return True


class CategoryField(Field):
    ''' Basic category field.'''
    def load(self, model_path, idx, category):
        ''' Loads the category field.

        Args:
            model_path (str): path to model
            idx (int): ID of data point
            category (int): index of category
        '''
        return category

    def check_complete(self, files):
        ''' Check if field is complete.
        
        Args:
            files: files
        '''
        return True


class ImagesField(Field):
    ''' Image Field.

    It is the field used for loading images.

    Args:
        folder_name (str): folder name
        transform (list): list of transformations applied to loaded images
        extension (str): image extension
        random_view (bool): whether a random view should be used
        with_camera (bool): whether camera data should be provided
        filename_pattern (str): pattern for prefix of the filename. Default ('*') allows any filename.
        image_based_hier (bool): If True, assumes a different kind of image folder hierarchy. This uses self.folder_name as the image dataset path
        and in practice, is used for the target domain dataset of images.
    '''
    def __init__(self, folder_name, transform=None,
                 extensions=['jpg'], random_view=True, with_camera=False, filename_pattern= "*", image_based_hier = False):
        self.folder_name = folder_name
        self.transform = transform
        self.extensions = extensions
        self.random_view = random_view
        self.with_camera = with_camera
        self.filename_pattern= filename_pattern 
        self.image_based_hier = image_based_hier
        # used only for image_based_hier folders. Saves time for glob
        self.files_cache = {}

    def load(self, model_path, idx, category):
        ''' Loads the data point.

        Args:
            model_path (str): path to model
            idx (int): ID of data point
            category (int): index of category
        '''
        
        if self.image_based_hier:
            # TODO: this extracts the class from model_path, and requires that it follows the format data/ShapeNet/03001627/713d6515...
            obj_class = model_path.split('/')[2]
            folder = os.path.join(self.folder_name, obj_class)

            if folder in self.files_cache:
                files = self.files_cache[folder]
            else:
                files = []
                for extension in self.extensions:
                    files_template = os.path.join(folder, '{}.{}'.format(self.filename_pattern, extension))
                    files += glob.glob(files_template)
                self.files_cache[folder] = files
                
        else:
            folder = os.path.join(model_path, self.folder_name)
            files = []
            for extension in self.extensions:
                files_template = os.path.join(folder, '{}.{}'.format(self.filename_pattern, extension))
                files += glob.glob(files_template)

        if self.random_view:
            #idx_img = random.randint(0, len(files)-1)
            # more efficient
            idx_img = int(random.random()*len(files))
        else:
            idx_img = 0
        filename = files[idx_img]

        image = Image.open(filename).convert('RGB')
        if self.transform is not None:
            image = self.transform(image)

        data = {
            None: image
        }

        if self.with_camera:
            camera_file = os.path.join(folder, 'cameras.npz')
            camera_dict = np.load(camera_file)
            Rt = camera_dict['world_mat_%d' % idx_img].astype(np.float32)
            K = camera_dict['camera_mat_%d' % idx_img].astype(np.float32)
            data['world_mat'] = Rt
            data['camera_mat'] = K

        return data

    def check_complete(self, files):
        ''' Check if field is complete.
        
        Args:
            files: files
        '''
        complete = (self.folder_name in files)
        # TODO: check camera
        return complete


# 3D Fields
class PointsField(Field):
    ''' Point Field.

    It provides the field to load point data. This is used for the points
    randomly sampled in the bounding volume of the 3D shape.

    Args:
        file_name (str): file name
        transform (list): list of transformations which will be applied to the
            points tensor
        with_transforms (bool): whether scaling and rotation data should be
            provided

    '''
    def __init__(self, file_name, transform=None, with_transforms=False, unpackbits=False):
        self.file_name = file_name
        self.transform = transform
        self.with_transforms = with_transforms
        self.unpackbits = unpackbits

    def load(self, model_path, idx, category):
        ''' Loads the data point.

        Args:
            model_path (str): path to model
            idx (int): ID of data point
            category (int): index of category
        '''
        file_path = os.path.join(model_path, self.file_name)

        points_dict = np.load(file_path)
        points = points_dict['points']
        # Break symmetry if given in float16:
        if points.dtype == np.float16:
            points = points.astype(np.float32)
            points += 1e-4 * np.random.randn(*points.shape)
        else:
            points = points.astype(np.float32)

        occupancies = points_dict['occupancies']
        if self.unpackbits:
            occupancies = np.unpackbits(occupancies)[:points.shape[0]]
        occupancies = occupancies.astype(np.float32)

        data = {
            None: points,
            'occ': occupancies,
        }

        if self.with_transforms:
            data['loc'] = points_dict['loc'].astype(np.float32)
            data['scale'] = points_dict['scale'].astype(np.float32)

        if self.transform is not None:
            data = self.transform(data)

        return data


class VoxelsField(Field):
    ''' Voxel field class.

    It provides the class used for voxel-based data.

    Args:
        file_name (str): file name
        transform (list): list of transformations applied to data points
    '''
    def __init__(self, file_name, transform=None):
        self.file_name = file_name
        self.transform = transform

    def load(self, model_path, idx, category):
        ''' Loads the data point.

        Args:
            model_path (str): path to model
            idx (int): ID of data point
            category (int): index of category
        '''
        file_path = os.path.join(model_path, self.file_name)

        with open(file_path, 'rb') as f:
            voxels = binvox_rw.read_as_3d_array(f)
        voxels = voxels.data.astype(np.float32)

        if self.transform is not None:
            voxels = self.transform(voxels)

        return voxels

    def check_complete(self, files):
        ''' Check if field is complete.
        
        Args:
            files: files
        '''
        complete = (self.file_name in files)
        return complete


class PointCloudField(Field):
    ''' Point cloud field.

    It provides the field used for point cloud data. These are the points
    randomly sampled on the mesh.

    Args:
        file_name (str): file name
        transform (list): list of transformations applied to data points
        with_transforms (bool): whether scaling and rotation dat should be
            provided
    '''
    def __init__(self, file_name, transform=None, with_transforms=False):
        self.file_name = file_name
        self.transform = transform
        self.with_transforms = with_transforms

    def load(self, model_path, idx, category):
        ''' Loads the data point.

        Args:
            model_path (str): path to model
            idx (int): ID of data point
            category (int): index of category
        '''
        file_path = os.path.join(model_path, self.file_name)

        pointcloud_dict = np.load(file_path)

        points = pointcloud_dict['points'].astype(np.float32)
        normals = pointcloud_dict['normals'].astype(np.float32)

        data = {
            None: points,
            'normals': normals,
        }

        if self.with_transforms:
            data['loc'] = pointcloud_dict['loc'].astype(np.float32)
            data['scale'] = pointcloud_dict['scale'].astype(np.float32)

        if self.transform is not None:
            data = self.transform(data)

        return data

    def check_complete(self, files):
        ''' Check if field is complete.
        
        Args:
            files: files
        '''
        complete = (self.file_name in files)
        return complete


# NOTE: this will produce variable length output.
# You need to specify collate_fn to make it work with a data laoder
class MeshField(Field):
    ''' Mesh field.

    It provides the field used for mesh data. Note that, depending on the
    dataset, it produces variable length output, so that you need to specify
    collate_fn to make it work with a data loader.

    Args:
        file_name (str): file name
        transform (list): list of transforms applied to data points
    '''
    def __init__(self, file_name, transform=None):
        self.file_name = file_name
        self.transform = transform

    def load(self, model_path, idx, category):
        ''' Loads the data point.

        Args:
            model_path (str): path to model
            idx (int): ID of data point
            category (int): index of category
        '''
        file_path = os.path.join(model_path, self.file_name)

        mesh = trimesh.load(file_path, process=False)
        if self.transform is not None:
            mesh = self.transform(mesh)

        data = {
            'verts': mesh.vertices,
            'faces': mesh.faces,
        }

        return data

    def check_complete(self, files):
        ''' Check if field is complete.
        
        Args:
            files: files
        '''
        complete = (self.file_name in files)
        return complete
