import maya.cmds as cmds
import maya.mel as mel
import xml.etree.ElementTree as et
import os
import getpass
import sys
from timeit import default_timer as timer

'''
A weight export/import tool inspired by some of the work I did while at Telltale Games. I found the tool useful enough
to recreate and adapt it for use outside of that specific workflow. Designed for Maya 2017 and above. Its strengths
are speed and the ability to being useful after topology changes. 

Special thanks to Chris Evans for figuring out some of incomplete documentation for Maya's deformerWeights command.
http://www.chrisevans3d.com/pub_blog/import-skin-weights-without-leaving-coffee/

TODO:
Be better about reporting when an empty file is exported. 
'''


class WeightTools:
    def __init__(self):
        self._version = '1.2.0'
        if sys.platform.startswith('win32'):
            self.platform = 'win32'
        elif sys.platform.startswith('linux'):
            self.platform = 'linux'
        elif sys.platform.startswith('darwin'):
            self.platform = 'darwin'
        else:
            cmds.error('Platform not supported.')

    def prune_weights(self, select_only=False):
        '''
        Calls the weight pruning stuff with a simple GUI.
        :return:
        '''
        sel = cmds.ls(sl=True, l=True)
        sel = [x for x in sel if cmds.listRelatives(x, c=True, type='shape') is not None]
        # If nothing is selected select every mesh in the scene.
        if len(sel) == 0:
            sel = cmds.ls(type='mesh')
            sel = [cmds.listRelatives(x, p=True, f=True)[0] for x in sel]
        result = cmds.promptDialog(
            title='Prune Weights',
            message='Prune Weights To How Many Influences?',
            text='4',
            button=['OK', 'Cancel'],
            defaultButton='OK',
            cancelButton='Cancel',
            dismissString='Cancel')
        if result == 'OK':
            limit = cmds.promptDialog(query=True, text=True)
        else:
            cmds.warning('User Aborted')
            cmds.waitCursor(st=False)
            return
        cmds.waitCursor(st=True)
        unclean_meshes = self.check_for_vert_influences(int(limit), *sel)[1]
        if not select_only:
            if len(unclean_meshes) == 0:
                cmds.warning('All Meshes Clean.')
                cmds.waitCursor(st=False)
                return
            self.prune_over_influenced_verts(int(limit), *unclean_meshes)
        else:
            if len(unclean_meshes) == 0:
                cmds.warning('All Meshes Clean')
            else:
                cmds.select(unclean_meshes, r=True)
        cmds.waitCursor(st=False)

    def check_for_vert_influences(self, limit, *items):
        '''
        Check for vertices with more than int:limit influences.
        :param limit:
        :param items:
        :return:
        '''
        unclean_meshes = []
        clean_meshes = []
        if type(limit) is not int:
            cmds.error('Please give type:int for argument: limit.')
        # Initialize Progress bar.
        if len(items) != 0:
            g_main_progress_bar = mel.eval('$tmp = $g_main_progress_bar')
            cmds.progressBar(g_main_progress_bar, edit=True, beginProgress=True, isInterruptable=True,
                             status='Starting up ...', minValue=0, maxValue=len(items))
            for item in items:
                if cmds.progressBar(g_main_progress_bar, query=True, isCancelled=True):
                    break
                cmds.progressBar(g_main_progress_bar, edit=True, status='Checking %s' % item)
                shapes = cmds.listRelatives(item, c=True, f=True, type='shape')
                if shapes is None:
                    continue
                shapes = list(set(shapes))
                for shape in shapes:
                    deformer = cmds.listConnections(shape, type='skinCluster')
                    if deformer is not None:
                        vtx_array = cmds.polyEvaluate(item, v=True)
                        if type(vtx_array) is int:
                            for vtx in range(vtx_array):
                                weights = cmds.getAttr('%s.wl[%s].weights' % (deformer[0], str(vtx)))[0]
                                weights = filter(lambda x: x != 0.0, weights)
                                if len(weights) > limit:
                                    unclean_meshes.append(item)
                                else:
                                    clean_meshes.append(item)
                        else:
                            cmds.warning('%s is not a poly object' % item)
                cmds.progressBar(g_main_progress_bar, edit=True, step=1)
            cmds.progressBar(g_main_progress_bar, edit=True, endProgress=True)
            return [list(set(clean_meshes)), list(set(unclean_meshes))]

    def prune_over_influenced_verts(self, limit=4, *items):
        '''
        Prunes lowest weighted influence from vertex.
        :param limit:
        :param items:
        :return:
        '''
        if type(limit) is not int:
            cmds.error('Please give type:int for argument: limit.')
        # Initialize Progress bar.
        items = [x for x in items if cmds.listRelatives(x, c=True, type='shape') is not None]
        if len(items) != 0:
            g_main_progress_bar = mel.eval('$tmp = $g_main_progress_bar')
            cmds.progressBar(g_main_progress_bar, edit=True, beginProgress=True, isInterruptable=True,
                             status='Starting up ...', minValue=0, maxValue=len(items))
            for item in items:
                if cmds.progressBar(g_main_progress_bar, query=True, isCancelled=True):
                    break
                cmds.progressBar(g_main_progress_bar, edit=True, status='Cleaning %s' % item)
                shapes = list(set(cmds.listRelatives(item, c=True, f=True, type='shape')))
                for shape in shapes:
                    deformer = cmds.listConnections(shape, type='skinCluster')
                    if deformer is not None:
                        cmds.skinPercent(deformer[0], shape, prw=0.0)
                        vtx_array = cmds.polyEvaluate(item, v=True)
                        for vtx in range(vtx_array):
                            influence_values = cmds.skinPercent(deformer[0], '%s.vtx[%s]' % (shape, str(vtx)), q=True,
                                                                value=True)
                            influences = cmds.skinCluster(deformer[0], q=True, inf=True)
                            influence_matrix = []
                            for i in range(len(influences)):
                                if influence_values[i] > 0:
                                    influence_matrix.append([influences[i], influence_values[i]])
                            influence_matrix = sorted(influence_matrix, key=lambda x: float(x[1]))
                            if (len(influence_matrix) - limit) > 0:
                                for i in range((len(influence_matrix) - limit)):
                                    cmds.skinPercent(deformer[0], '%s.vtx[%s]' % (shape, str(vtx)),
                                                     tv=[(influence_matrix[i][0], 0.0)])
                cmds.progressBar(g_main_progress_bar, edit=True, step=1)
            cmds.progressBar(g_main_progress_bar, edit=True, endProgress=True)

    def remap_weights(self, source=None, target=None, path=None, write_path=None):
        '''
        Remaps weights from one XML to another based on two lists of equal size.
        If a source and target element are equal (source = ['foo'], target = ['foo']) an empty subelement is created.
        :param source:
        :param target:
        :param path:
        :param write_path:
        :return:
        '''
        # Gets the local user temp directory if no path is given.
        if write_path is None:
            write_path = 'C:/Users/%s/AppData/Local/Temp/%s' % (getpass.getuser(), path.rsplit('/', 1)[1])
        input_xml = et.parse(path)
        root = input_xml.getroot()
        layer = 0
        deformer_location = root.find('.//*[@deformer]')
        deformer = deformer_location.get('deformer')
        shape_location = root.find('.//*[@shape]')
        shape = shape_location.get('shape')
        # The deformerWeights command looks for the highest index value as an attribute.
        # We keep an eye out for that as we loop through.
        highest_index = 0
        for joint in source:
            source_index = {}
            target_index = {}
            if target[source.index(joint)] is not joint:
                for weight in root.findall('weights'):
                    # Here we get the info from the source joint.
                    if joint == weight.get('source'):
                        for child in weight:
                            source_index[int(child.get('index'))] = child.get('value')
                            if int(child.get('index')) > int(highest_index):
                                highest_index = child.get('index')
                    # Here we get info from the target joint.
                    if target[source.index(joint)] == weight.get('source') and weight.get('size') != '0':
                        for child in weight:
                            target_index[int(child.get('index'))] = child.get('value')
                            if int(child.get('index')) > int(highest_index):
                                highest_index = child.get('index')
                    # If the joint doesn't exist in the target list (probably not in the deformer), remove it.
                    if weight.get('source') not in target and weight.get('source') in source:
                        root.remove(weight)
                # Now we loop through the keys that we generated and assign weight values.
                for element in target_index:
                    if element not in source_index:
                        # Append the value if the index doesn't already exist
                        source_index[element] = target_index[element]
                    else:
                        # Get the sum of the values if the is already in the dictionary.
                        source_index[element] = str(float(source_index[element]) + float(target_index[element]))
                        # If the sum > than 1, clamp it at one (shouldn't happen but may be needed for Post Normalization)
                        if source_index[element] > 1:
                            source_index[element] = 1
            else:
                et.SubElement(root, "weights", attrib={"source": joint, "max": "0", "size": "0", "layer": "0",
                                                       "defaultValue": "0.00", "shape": shape, "deformer": deformer})
            # loops through target joints
            for weight in root.findall('.//*[@source="%s"]' % target[source.index(joint)]):
                # Here we clean out the subelements so they can be added in the correct index order.
                attrib = {}
                keys = weight.keys()
                for attr in keys:
                    attrib[attr] = weight.get(attr)
                weight.clear()
                # Here we set the correct attributes
                for attr in keys:
                    weight.set(attr, attrib[attr])
                # Here we recreate the subelements
                for element in sorted(source_index.keys()):
                    et.SubElement(weight, "point", attrib={"index": str(element), "value": str(source_index[element])})
                weight.set("size", str(len(weight)))
                weight.set("max", str(highest_index))
        for weight in root.findall('weights'):
            weight.set("layer", str(layer))
            layer += 1
        output = et.ElementTree(root)
        output.write(write_path, xml_declaration=True)
        return write_path

    def check_weights(self, deformer=None, path=None):
        '''
        Checks deformers against XML files to find incompatibilities
        :param deformer:
        :param path:
        :return:
        '''
        input_xml = et.parse(path)
        root = input_xml.getroot()
        joints = []
        # Here we get the names of the joints in the file.
        for weight in root.findall('weights'):
            joints.append(weight.get('source'))
        # If a deformer wasn't given just return the joints in the file.
        if deformer is None:
            return joints
        # If a deformer is given compare the file against the deformer.
        else:
            # Here we get the joints on the current deformer.
            skin_joints = cmds.listConnections(deformer, type='joint')
            # Here we check to see if there are joints in the file that aren't in the deformer and visa versa.
            missing_from_skin = [x for x in joints if x not in skin_joints]
            missing_from_file = [x for x in skin_joints if x not in joints]
            return [list(set(missing_from_skin)), list(set(missing_from_file))]

    def weight_export(self, path=None, items=None, batch=False):
        '''
        Export weights to a path. Outputs an XML.
        :param path :
        :param items:
        :param batch:
        :return:
        '''
        # If no items are given look for selected objects.
        if items is None:
            if not batch:
                sel = cmds.ls(sl=True, l=True)
            else:
                sel = [cmds.listRelatives(sel, ad=True, f=True, typ='transform') for sel in cmds.ls(sl=True, l=True)]
                sel = [subelement for element in sel for subelement in element]
        else:
            if type(items) is not []:
                set(items)
            sel = items
        # If no path is given open a GUI
        if path is None:
            if len(sel) == 1:
                input_xml = cmds.fileDialog2(ds=2, ff='*.xml', fm=0, okc='Save')
                if input_xml is None:
                    cmds.warning('User Canceled')
                    return
                else:
                    input_xml = input_xml[0]
                absolute_path = input_xml.rsplit('/', 1)[0]
                path = input_xml.rsplit('/', 1)[1]
            else:
                input_xml = cmds.fileDialog2(ds=2, fm=3, okc='Save')
                if input_xml is None:
                    cmds.warning("User Canceled")
                    return
                else:
                    input_xml = input_xml[0]
                input_xml = input_xml.replace('\\', '/')
                absolute_path = input_xml.rsplit('/', 1)[0] + '/'
                path = input_xml.rsplit('/', 1)[1] + '/'
                # Attempt to correct path in case user selected a child of the root directory
                if sel[0].split('|', 2)[1] in path:
                    path = ''
        else:
            absolute_path = path
        start_time = timer()
        if len(sel) != 0:
            # Initialize Progress bar.
            g_main_progress_bar = mel.eval('$tmp = $gMainProgressBar')
            cmds.progressBar(g_main_progress_bar, edit=True, beginProgress=True, isInterruptable=True,
                             status='Starting up ...', maxValue=len(sel))
            skip_dialog = False
            # If there is only one object go this way.
            if len(sel) == 1:
                # Get shapes
                shapes = cmds.listRelatives(sel[0], type='shape', f=True)
                if shapes is not None:
                    # Find deformers attached to the shapes
                    deformer = None
                    for shape in shapes:
                        connections = cmds.listHistory(shape)
                        for item in connections:
                            if cmds.objectType(item) == 'skinCluster':
                                deformer = item
                                break
                    if deformer is not None:
                        # If the file already exists confirm overwrite.
                        if os.path.exists('%s%s.xml' % (absolute_path, path)):
                            # Check if path is writable.
                            if os.access('%s%s.xml' % (absolute_path, path), os.W_OK):
                                # Export weights to XML.
                                cmds.deformerWeights(path, p=absolute_path, ex=True, vc=True, deformer=deformer)
                                print 'Writing %s/%s' % (absolute_path, path)
                            else:
                                cmds.warning('%s/%s not writeable. Check Permissions' % (
                                    absolute_path, path))
                                return
                        else:
                            cmds.deformerWeights(path, p=absolute_path, ex=True, vc=True, deformer=deformer)
                            print 'Writing %s%s' % (absolute_path, path)
                    else:
                        cmds.warning('Could not find deformer on %s' % sel[0])
                else:
                    cmds.warning('Could not find shape under %s' % sel[0])
            # Otherwise go this way.
            else:
                for selection in sel:
                    selection_path = selection[1:].replace('|', '/')
                    selection_path = selection_path.replace(':', '_')
                    deformer = None
                    cmds.waitCursor(st=True)
                    shapes = cmds.listRelatives(selection, type='shape', f=True)
                    if cmds.progressBar(g_main_progress_bar, query=True, isCancelled=True):
                        break
                    if shapes is not None:
                        shapes = cmds.listRelatives(selection, type='shape', f=True)
                        if shapes is not None:
                            for shape in shapes:
                                connections = cmds.listHistory(shape)
                                for item in connections:
                                    if cmds.objectType(item) == 'skinCluster':
                                        deformer = item
                                        break
                        if deformer is not None:
                            try:
                                # If the file already exists confirm overwrite.
                                if os.path.exists('%s%s%s' % (absolute_path, path, selection_path.rsplit('/', 1)[0])):
                                    if os.path.exists(
                                            '%s%s%s.xml' % (absolute_path, path, selection_path)):
                                        # Check if path is writable.
                                        if os.access('%s%s%s.xml' % (absolute_path, path, selection_path),
                                                     os.W_OK):
                                            pass
                                        else:
                                            cmds.warning('%s%s%s not writeable. Check Permissions' % (
                                                absolute_path, path, selection[1:].replace('|', '/')))
                                            continue
                                        # If we're not skipping the dialog
                                        if not skip_dialog:
                                            dialog = cmds.confirmDialog(title='Confirm',
                                                                        message='../%s%s.xml already exists, overwrite?' %
                                                                                (path, selection_path),
                                                                        button=['Yes(All)', 'Yes', 'No'],
                                                                        defaultButton='Yes',
                                                                        cancelButton='No',
                                                                        dismissString='No')
                                            if dialog == 'Yes(All)':
                                                skip_dialog = True
                                            if 'Yes' in dialog:
                                                cmds.progressBar(g_main_progress_bar,
                                                                 edit=True,
                                                                 status='Writing %s%s%s' %
                                                                        (absolute_path, path,
                                                                         selection_path))
                                                cmds.deformerWeights((selection_path + '.xml'),
                                                                     p=absolute_path + path,
                                                                     ex=True, vc=True,
                                                                     deformer=deformer)
                                        # If we are.
                                        else:
                                            cmds.progressBar(g_main_progress_bar, edit=True, status=(
                                                    'Writing %s%s%s' % (absolute_path, path, selection_path)))
                                            cmds.deformerWeights((selection_path + '.xml'),
                                                                 p=absolute_path + path, ex=True, vc=True,
                                                                 deformer=deformer)
                                    else:
                                        cmds.progressBar(g_main_progress_bar, edit=True,
                                                         status=('Writing %s%s%s' % (
                                                             absolute_path, path, selection_path)))
                                        cmds.deformerWeights(selection_path + '.xml', p=absolute_path + path, vc=True,
                                                             ex=True,
                                                             deformer=deformer)
                                else:
                                    # If the object doesn't have deformers but has children try and make a place for it
                                    # in the hierarchy.
                                    try:
                                        os.makedirs('%s%s%s' % (absolute_path, path, selection_path.rsplit('/', 1)[0]))
                                    except WindowsError:
                                        pass
                                    cmds.progressBar(g_main_progress_bar, edit=True, status=(
                                            'Writing %s%s%s' % (absolute_path, path, selection_path)))
                                    cmds.deformerWeights(selection_path + '.xml',
                                                         p=absolute_path + path,
                                                         ex=True, vc=True, deformer=deformer)
                            except (TypeError, ValueError, RuntimeError):
                                cmds.warning('Failed to export %s' % (selection_path))
                    # Clean up
                    cmds.waitCursor(st=False)
                    cmds.progressBar(g_main_progress_bar, edit=True, step=1)
            end_time = timer()
            cmds.progressBar(g_main_progress_bar, edit=True, endProgress=True)
            print ('Exported %s weights in %s seconds.' % (len(sel), end_time - start_time))

    def weight_import(self, path=None, items=None, batch=False, clean_up=True):
        '''
        Import weights from path, or finding none open a GUI
        :param path:
        :param items:
        :param batch:
        :param clean_up:
        :return:
        '''
        # If no items are given look for selected objects.
        if items is None:
            if batch:
                sel = cmds.ls(sl=True, l=True)
                # Look to see if the selection has children and add them to the list if they do.
                sel_dec = [cmds.listRelatives(x, ad=True, f=True, typ='transform') for x in sel]
                sel_dec = filter(None, sel_dec)
                sel_dec = [subelement for element in sel_dec for subelement in element]
                sel.extend(sel_dec)
            else:
                sel = cmds.ls(sl=True, l=True)
        else:
            if type(items) is not []:
                set(items)
            sel = items
        # If no path is given open a GUI
        if path is None:
            if len(sel) == 1:
                input_xml = cmds.fileDialog2(ds=2, ff='*.xml', fm=1, okc='Open')
                if input_xml is None:
                    cmds.warning('User Canceled')
                    return
                else:
                    absolute_path = input_xml[0]
            else:
                input_xml = cmds.fileDialog2(ds=2, fm=3, okc='Open')
                if input_xml is None:
                    cmds.warning("User Canceled")
                    return
                else:
                    input_xml = input_xml[0]
                absolute_path = input_xml.replace('\\', '/')

        else:
            absolute_path = path
        if not os.path.exists(absolute_path):
            cmds.error('Specified path not found.')
        repath_auto = False
        report = []
        skip = 0
        temp_paths = []
        start_time = timer()
        if len(sel) != 0:
            # Select application method.
            method = cmds.confirmDialog(title='Select Method',
                                        message='Which method should be used to apply the weights?',
                                        button=['Index', 'Nearest', 'Over', 'Barycentric', 'Bilinear', 'Cancel'],
                                        defaultButton='Index',
                                        cancelButton='Cancel', dismissString='Cancel')
            if method == 'Cancel':
                cmds.error('Aborting Weight Import.')
            # Initialize Progress Bar
            if len(sel) > 1:
                max_value = len(sel)
            else:
                max_value = len(sel) + 1
            g_main_progress_bar = mel.eval('$tmp = $gMainProgressBar')
            cmds.progressBar(g_main_progress_bar, edit=True, beginProgress=True, isInterruptable=True,
                             status='Starting up ...', maxValue=max_value)
            paths = {}
            for (dirpath, dirnames, filenames) in os.walk(absolute_path):
                for file in filenames:
                    dirpath = dirpath.replace('\\', '/')
                    if '.xml' in file:
                        key = '%s/%s/%s' % (dirpath.split('/')[-2], dirpath.split('/')[-1], file)
                        full_path = '%s/%s' % (dirpath, file)
                        paths[key] = full_path
            for selection in sel:
                cmds.waitCursor(st=True)
                path_in = None
                # Find shapes
                shapes = cmds.listRelatives(selection, type='shape', f=True)
                if cmds.progressBar(g_main_progress_bar, query=True, isCancelled=True):
                    break
                if shapes is not None:
                    # Find out whether we need to specify and object or not.
                    if '.xml' in absolute_path:
                        path_in = '/%s' % absolute_path.rsplit('/', 1)[1]
                        absolute_path = absolute_path.rsplit('/', 1)[0]
                    else:
                        try:
                            key = '%s/%s/%s.xml' % (
                                selection.split('|')[-3], selection.split('|')[-2], selection.split('|')[-1])
                            path = paths[key]
                            absolute_path = path.rsplit('/', 1)[0]
                            path_in = '/%s' % path.rsplit('/', 1)[1]
                        except KeyError:
                            short_name = selection.split('|')[-1]
                            for key in paths.keys():
                                if short_name in key:
                                    if not repath_auto:
                                        autopath_result = cmds.confirmDialog(t='Path Not Found',
                                                                             m='I could not find a file corresponding to:\n\n %s\n\n Would you like to use:\n\n %s?' % (
                                                                                 selection[1:].replace('|', '/'), key),
                                                                             button=['Yes', 'Yes to All', 'No',
                                                                                     'No to All'],
                                                                             cancelButton='No')

                                    if 'Yes' in autopath_result:
                                        path = paths[key]
                                        absolute_path = path.rsplit('/', 1)[0]
                                        path_in = '/%s' % path.rsplit('/', 1)[1]
                                        if autopath_result == 'Yes to All':
                                            repath_auto = True
                                    elif autopath_result == 'No to All':
                                        repath_auto = True
                                        break
                                    else:
                                        continue
                    if path_in is None:
                        skip += 1
                        continue
                    if os.path.exists(absolute_path + path_in):
                        # Check if file is readable
                        if os.access(absolute_path + path_in, os.R_OK):
                            pass
                        else:
                            cmds.warning('%s%s not readable. Check Permissions' % (absolute_path, path_in))
                            cmds.waitCursor(st=False)
                            continue
                    else:
                        report.append((absolute_path + path_in))
                        cmds.waitCursor(st=False)
                        continue
                    # find deformers
                    deformer = None
                    for shape in shapes:
                        connections = cmds.listHistory(shape)
                        for item in connections:
                            if cmds.objectType(item) == 'skinCluster':
                                deformer = item
                                break
                    if deformer is not None:
                        try:
                            cmds.progressBar(g_main_progress_bar, edit=True, beginProgress=True, isInterruptable=True,
                                             status='Checking map ...', maxValue=max_value)
                            # Check deformer against xml membership.
                            results = self.check_weights(deformer, path=absolute_path + path_in)
                            # Add the joints missing from file to sources and targets so that deformerWeights is happy.
                            sources = results[1]
                            targets = [x for x in results[1]]
                            # If there are joints missing from the deformer launch a gui for retargeting.
                            if len(results[0]) > 0:
                                cmds.progressBar(g_main_progress_bar, edit=True, beginProgress=True,
                                                 isInterruptable=True,
                                                 status='Remapping weights ...', maxValue=len(sel))
                                for item in results[0]:
                                    # Gui elements
                                    button = cmds.promptDialog(title='%s not found...' % item,
                                                               message='Which joint should inherit the weights?',
                                                               text='Please input a joint', button=['OK', 'Cancel'],
                                                               defaultButton='OK', dismissString='Cancel')
                                    if button == 'OK':
                                        result = cmds.promptDialog(q=True, text=True)
                                        if result == 'Please input a joint':
                                            results[0].append(item)
                                            continue
                                        else:
                                            sources.append(item)
                                            targets.append(result)
                                    else:
                                        cmds.warning('Skipping %s' % path_in)
                                        skip += 1
                                        continue
                                # Remap the weights and update the paths
                                path_in = self.remap_weights(sources, targets, path=absolute_path + '/' + path_in)
                                absolute_path = path_in.rsplit('/', 1)[0]
                                path_in = '/' + path_in.rsplit('/', 1)[1]
                                temp_paths.append(absolute_path + path_in)
                                cmds.warning('New path is %s' % (absolute_path + path_in))
                            elif len(results[1]) > 0:
                                cmds.progressBar(g_main_progress_bar, edit=True, beginProgress=True,
                                                 isInterruptable=True,
                                                 status='Remapping weights ...', maxValue=max_value)
                                path_in = self.remap_weights(sources, targets, path=absolute_path + '/' + path_in)
                                absolute_path = path_in.rsplit('/', 1)[0]
                                path_in = '/' + path_in.rsplit('/', 1)[1]
                                temp_paths.append(absolute_path + path_in)
                                cmds.warning('New path is %s' % (absolute_path + path_in))

                            cmds.progressBar(g_main_progress_bar, edit=True,
                                             status='Loading ' + (absolute_path + path_in))
                            # Import the weights.
                            if len(sel) == 1:
                                cmds.deformerWeights(path_in, p=absolute_path, im=True, method=method.lower(),
                                                     deformer=deformer)
                            else:
                                cmds.deformerWeights(path_in, p=absolute_path, im=True, method=method.lower(),
                                                     deformer=deformer)
                            # Normalize weights
                            cmds.skinPercent(deformer, selection, normalize=True)
                            print 'Imported %s to %s' % (absolute_path + path_in, selection)
                        except WindowsError:
                            report.append((absolute_path + path_in))
                            skip += 1
                    else:
                        skip += 1
                else:
                    skip += 1
                cmds.progressBar(g_main_progress_bar, edit=True, step=1)
                cmds.waitCursor(st=False)
            # Clean up
            temp_paths = list(set(temp_paths))
            if clean_up:
                if len(temp_paths) > 0:
                    for path in temp_paths:
                        try:
                            os.remove(path)
                        except WindowsError:
                            print ('Failed to clean up %s' % path)
            # Print reports of failures.
            if len(report) > 0:
                for r in report:
                    print ('Could not find file: ' + r)
                cmds.progressBar(g_main_progress_bar, edit=True, endProgress=True)
                cmds.warning('Some weight files could not be found. Check output for details.')
            else:
                cmds.progressBar(g_main_progress_bar, edit=True, endProgress=True)
            end_time = timer()
            print ('Imported %s weights in %s seconds.' % (len(sel) - skip, end_time - start_time))

    def bind_from_file(self, path=None, items=None, batch=False):
        '''
        Binds the items in [items] to the joints in file if they exist.
        :param path:
        :param selection:
        :return:
        '''
        if items is None:
            if batch:
                sel = cmds.ls(sl=True, l=True)
                # Look to see if the selection has children and add them to the list if they do.
                sel_dec = [cmds.listRelatives(x, ad=True, f=True, typ='transform') for x in sel]
                sel_dec = filter(None, sel_dec)
                sel_dec = [subelement for element in sel_dec for subelement in element]
                sel.extend(sel_dec)
            else:
                sel = cmds.ls(sl=True, l=True)
        else:
            if type(items) is not []:
                set(items)
            sel = items
        # If no path is given open a GUI
        if path is None:
            if len(sel) == 1:
                input_xml = cmds.fileDialog2(ds=2, ff='*.xml', fm=1, okc='Open')
                if input_xml is None:
                    cmds.warning('User Canceled')
                    return
                else:
                    absolute_path = input_xml[0]
            else:
                input_xml = cmds.fileDialog2(ds=2, fm=3, okc='Open')
                if input_xml is None:
                    cmds.warning("User Canceled")
                    return
                else:
                    input_xml = input_xml[0]
                absolute_path = input_xml.replace('\\', '/')

        else:
            absolute_path = path
        if not os.path.exists(absolute_path):
            cmds.error('Specified path not found.')

        # Initialize Progress Bar
        if len(sel) > 1:
            max_value = len(sel)
        else:
            max_value = len(sel) + 1
        g_main_progress_bar = mel.eval('$tmp = $gMainProgressBar')
        cmds.progressBar(g_main_progress_bar, edit=True, beginProgress=True, isInterruptable=True,
                         status='Starting up ...', maxValue=max_value)
        paths = {}
        for (dirpath, dirnames, filenames) in os.walk(absolute_path):
            for file in filenames:
                dirpath = dirpath.replace('\\', '/')
                if '.xml' in file:
                    key = '%s/%s/%s' % (dirpath.split('/')[-2], dirpath.split('/')[-1], file)
                    full_path = '%s/%s' % (dirpath, file)
                    paths[key] = full_path
        for selection in sel:
            cmds.waitCursor(st=True)
            path_in = None
            if cmds.progressBar(g_main_progress_bar, query=True, isCancelled=True):
                break
            # Find out whether we need to specify and object or not.
            if '.xml' in absolute_path:
                path_in = '/%s' % absolute_path.rsplit('/', 1)[1]
                absolute_path = absolute_path.rsplit('/', 1)[0]
            else:
                try:
                    key = '%s/%s/%s.xml' % (
                        selection.split('|')[-3], selection.split('|')[-2], selection.split('|')[-1])
                    path = paths[key]
                    absolute_path = path.rsplit('/', 1)[0]
                    path_in = '/%s' % path.rsplit('/', 1)[1]
                except KeyError:
                    short_name = selection.split('|')[-1]
                    for key in paths.keys():
                        if short_name in key:
                            if not repath_auto:
                                autopath_result = cmds.confirmDialog(t='Path Not Found',
                                                                     m='I could not find a file corresponding to:\n\n %s\n\n Would you like to use:\n\n %s?' % (
                                                                         selection[1:].replace('|', '/'), key),
                                                                     button=['Yes', 'Yes to All', 'No',
                                                                             'No to All'],
                                                                     cancelButton='No')

                            if 'Yes' in autopath_result:
                                path = paths[key]
                                absolute_path = path.rsplit('/', 1)[0]
                                path_in = '/%s' % path.rsplit('/', 1)[1]
                                if autopath_result == 'Yes to All':
                                    repath_auto = True
                            elif autopath_result == 'No to All':
                                repath_auto = True
                                break
                            else:
                                continue
            if path_in is None:
                continue
            if os.path.exists(absolute_path + path_in):
                # Check if file is readable
                if os.access(absolute_path + path_in, os.R_OK):
                    pass
                else:
                    cmds.warning('%s%s not readable. Check Permissions' % (absolute_path, path_in))
                    cmds.waitCursor(st=False)
                    continue
                joints = [x for x in self.check_weights(path=absolute_path + path_in) if cmds.objExists(x)]
                # If there are joints in the scene attempt to bind to them.
                if len(joints) > 0:
                    try:
                        cmds.skinCluster(joints, selection, bm=0, omi=False, sm=0, tsb=True, nw=1,
                                         ihs=True)
                    except RuntimeError:
                        cmds.warning('Could not skin %s' % selection)

            else:
                cmds.waitCursor(st=False)
                continue
            cmds.progressBar(g_main_progress_bar, edit=True, step=1)
            cmds.waitCursor(st=False)
        else:
            cmds.progressBar(g_main_progress_bar, edit=True, endProgress=True)