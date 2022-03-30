import os
import regex as re
import pandas as pd
import re
from itertools import islice, chain
import csv
from collections import defaultdict
import pickle


class ScriptScraper():
    """
    Scraping script files to determine set of input, baseline data files, & test parameters
    required per unique UFS application-to-physics build per unique reqression test.
    
    """
    def __init__(self, local_repo_folder):

        # Main reference table featuring apps-to-physics_suite builds & their associated tests. 
        # Extracted from main script file, rt.conf, to reference.
        self.main_reference = "AppSuiteCombo2Test.csv"
        
        #*TODO: Since NOAA's dev team makes revisions to rt.conf & remove/add /tests/tests files. Will have to
        # read directly from the rt.conf file & set to "main_reference" for the mapping of UFS app-to-tests 
        #self.main_reference = '101821/ufs-weather-model-develop/ufs-weather-model-develop/tests/rt.conf'
        
        # Files comprised of info. regarding UFS apps & tests relationship to datasets.
        self.local_repo_folder = local_repo_folder
        self.ufs_tests_root_dir = '/tests'
        self.test_scripts_dir = f'{self.local_repo_folder}{self.ufs_tests_root_dir}/tests'
        self.fv3_conf_dir = f'{self.local_repo_folder}{self.ufs_tests_root_dir}/fv3_conf'
        self.parm_conf_dir = f'{self.local_repo_folder}{self.ufs_tests_root_dir}/parm'
        self.input_data_dirs = [self.test_scripts_dir, 
                                self.fv3_conf_dir, 
                                self.parm_conf_dir]
        
    def read_appsphys2test(self):
        """
        Reads lines comprised of application-to-physics suite builds & their associated tests.
        
        Args:
            None
            
        Return (list): List of raw text containing application-to-physics 
        suite build & test names.
            
        """
        
        # Extract apps-to-physics_suite build & test names.
        ref_txt = []
        with open(self.main_reference, mode='r') as file:
            csv_obj = csv.reader(file)
            hdr = next(csv_obj)
            for lines in csv_obj:
                tokenize_fn = []
                tokenize_fn = [x.strip() for x in lines[-1].split(",")]
                ref_txt.append(lines[:3] + tokenize_fn)

        return ref_txt

    def nested_dict(self):
        """
        Subroutine to generate nested dictionary from nested list of texts.
        
        Args: 
            None
            
        Return (dict): Nested dictionary. 
        
        Note: Method is called by 'convert_ist2dict()' method.
        
        """
        return defaultdict(self.nested_dict)

    def convert_list2dict(self, ref_txt):
        """
        Convert nested list to nested dictionary.
        
        Args:
            ref_txt (list): List of raw text containing UFS application-to-physics 
                            suite build & regression test names.

        Return (dict): Nested dictionary of the nested list of texts ("ref_txt").

        """
        
        # Create nested dictionary of list of raw text.
        nested = self.nested_dict()
        for k in ref_txt:
            nested[k[0]][k[1]].update({k[2]: list(k[3:])})

        return nested

    def get_app2test(self, nested_dict):
        """
        Restructure app2test nested dictionary.
        
        Args:
            nested_dict (dict): Nested dictionary of the nested list of texts ("ref_txt").

        Return (dict): The reconfigured nested dictionary of the nested list of texts ("ref_txt")
        into apps-to-physics_suite build to their corresponding regression tests.

        """

        # UFS apps-to-physics_suite build & their corresponding tests.
        combo_dict = {}
        for app, app_info in nested_dict.items():
            for physics_suite, tests in app_info.items():
                combo_dict[app, physics_suite] = tests
        
        return combo_dict

    def get_rtinfo(self, appsphys2test_dict):
        """
            RT framework information overview.

        Args:
            appsphys2test_dict (dict): Reconfigured nested dictionary of the nested
            list of texts  ("ref_txt") consisting of the apps-to-physics_suite build to
            their corresponding tests.

        Return: None

        """
        
        # Initialize counters for total UFS app-to-physics suite builds & tests.
        app2phys_counter = 0
        cat_counter = 0
        test_counter = 0
        unique_tests = []
        for k,v in appsphys2test_dict.items():
            app2phys_counter = len(appsphys2test_dict.keys())
            cat_counter += len(v)
            
            # Extract test names per UFS App-to-Physics Suite build.
            test_names = [test for test in v.values()]
            test_names = set(list(chain.from_iterable(test_names)))
            unique_tests.append(test_names)
            
            # Total tests for all UFS App-to-Physics Suite builds.
            test_counter += len(test_names)    
            
        unique_tests = set(list(chain.from_iterable(unique_tests)))
        print(f"Total unique UFS App-to-Physics Suite builds:\n {app2phys_counter}\n")
        print(f"Total number of tests (if performing tests for all UFS App-to-Physics Suite builds):\n {test_counter}\n")
        print(f"Total unique tests overall (per current rt.conf):\n {len(unique_tests)}\n")
        print(f"List of unique tests present (per current rt.conf):\n {unique_tests}\n")
        print(f"Total unique categories (UFS App-to-Physics Suite builds to Test_Type):\n {cat_counter}\n")
        
        return

    def read_raw_filenames(self):
        """
        Reads raw text comprised of information regarding the data files required by each regression test.
        
        Args: 
            None
            
        Return (dict): Dictionary for referencing sets of data files required per regression
        test.
        
        The configuration for data files to be copied, moved, rsync, and/or linked is set within
        the /fv3_conf files. The configuration for data files set to namelist variables are set 
        within the /parm files.
            
        """
        
        # Extract raw test from /parm, /fv3_conf, and /tests folder comprised of config. files.
        raw_data_dict = {}
        for config_folder in self.input_data_dirs:

            # Clear dict for each config. folder
            raw_txt_dict = {}
            
            # Locate & record only files.
            for item in os.scandir(config_folder):
                if item.is_file(): 
                    
                    # Read each file and partition text line-by-line.
                    idx = 0
                    raw_txt_list =[]
                    file = open(config_folder + '/' + item.name,"r")
                    for line in file:
                        raw_txt_list.append(line)
                    
                    # Raw text per files in /parm, /fv3_conf, and /tests.
                    raw_txt_dict[item.name] = raw_txt_list
            

            # Dictionary of all text in /parm, /fv3_conf, and /tests.
            raw_data_dict[os.path.basename(config_folder)] = raw_txt_dict

        return raw_data_dict
    
    def read_tests_fv3_parms(self, prefix_list = ['cp', 'mv', 'rsync','ln']):
        """
        Reads lines comprised of data filenames in the /fv3_conf, /parm, and /tests files.
        
        Args: 
            None
            
        Return (dict): Dictionary for referencing sets of input data files being used per test.
        
        Referencing the UFS-WM RT framework, the variable, CNTL_DIR, w/in each /tests file 
        will declare the name of the baseline dataset folder required for the given regression
        test. The variables following the variable, "export_," w/in each /tests file will set
        variables overwriting the "default_vars.sh" variables required for the given regression
        test's configuration files.
        
        """
        input_data_dict = {}
        raw_data_dict = {}

        # Scan each folder (e.g. /parm, /fv3_conf) comprised of configuration files.
        for config_folder in self.input_data_dirs:

            # Clear dict for each config. folder
            config_file_dict = {}
            
            # Read each /tests script file.
            if os.path.basename(config_folder) == 'tests':

                # Locate & record only files.
                for item in os.scandir(config_folder):
                    if item.is_file(): 
                        file = open(config_folder + '/' + item.name, "r+")
                        
                        # Append only lines setting the config. params and CNTL directory.
                        relevant_txt = []
                        cntl_dir = ''
                        for idx, line in enumerate(file):
                            line = line.lstrip()
                            
                            # Extract baseline dataset folder. 
                            if "CNTL_DIR" in line:
                                cntl_dir = line
                                
                            # Extract variables required for test's config files.
                            if "export_" in line:
                                default_method = line
                                relevant_txt.append(cntl_dir + default_method + "".join(islice(file, None)))
      
                        # Set all relevant text mentioned within given /tests script file.
                        config_file_dict[item.name] = relevant_txt 

                # Dictionary of text lines copying files.
                input_data_dict[os.path.basename(config_folder)] = self.preprocess_tests(config_file_dict)

            # Read each /fv3_conf file.
            if os.path.basename(config_folder) == 'fv3_conf':

                # Locate & record only files.
                for item in os.scandir(config_folder):
                    if item.is_file(): 
                        line_num_list=[]
                        line_txt_list=[]
                        file = open(config_folder + '/' + item.name, "r")

                        # Append only lines copying data files.
                        for idx, line in enumerate(file):
                            line = line.lstrip()
                            if line.startswith(tuple(prefix_list)):
                                line_num_list.append(idx + 1)
                                line_txt_list.append(line.lstrip())

                        # Without line numbers corresponding to copied input data files.
                        config_file_dict[item.name] = line_txt_list 

                        # Lines mentioning input data files in config. file
                        #linenum2linetxt = dict(zip(line_num_list, line_txt_list))                             
                        #config_file_dict[item.name] = linenum2linetxt

                # Preprocess fv3 dictionary of text lines copying, sync, mv, ln files.
                input_data_dict['fv3_conf'] = self.preprocess_fv3(config_file_dict)
                input_data_dict[os.path.basename(config_folder)] = input_data_dict['fv3_conf']

            # Read each /parm file.
            if os.path.basename(config_folder) == 'parm':

                # Locate & record only files.
                for item in os.scandir(config_folder):
                    if item.is_file(): 

                        # Read each file.
                        line_txt_list=[]
                        file = open(config_folder + '/' + item.name, "r")

                        # Append only lines setting/stating .ext files.
                        # Filters out comments via removal of text after comment annotation, !.
                        files4parm = []
                        for idx, line in enumerate(file):
                            line = line.lstrip()
                            
                            # Append only non-commented txt mentioning data files.
                            if line.startswith("!")==False and "!" in line and "=" in line:
                                x_noncomment_idx = line.index("!")
                                line = line[:x_noncomment_idx+1]   
                                for x in line.split():
                                    files4line = []
                                    
                                    # Create list per line as some parm files will set to list of more than one 
                                    # filename. NOTE: MOM6 list of parm files are not delimited by spaces 
                                    # between commas.
                                    x = x.split(",")
                                    for x_sep in x:
                                        if any(r in x_sep for r in ['.nc', '.grib', '.grb']):
                                            files4line.append(x_sep.replace("'", "").replace('"', '').replace(",", ""))
                                            files4parm.append(files4line)
                                
                            elif line.startswith("!")==False and '=' in line: 
                                for x in line.split():
                                    files4line = []

                                    # Create list per line as some parm files will set to list of more than one
                                    # filename. NOTE: MOM6 list of parm files are not delimited by spaces between
                                    # commas.
                                    x = x.split(",")
                                    for x_sep in x:
                                        if any(r in x_sep for r in ['.nc', '.grib', '.grb']):
                                            files4line.append(x_sep.replace("'", "").replace('"', '').replace(",", ""))
                                            files4parm.append(files4line)

                        # Set all relevant text mentioned within given /parm script file.
                        config_file_dict[item.name] = list(map(''.join, files4parm))

                # Dictionary of text lines setting namelist variables to a data filename.
                input_data_dict[os.path.basename(config_folder)] = config_file_dict

        return input_data_dict
    
    def get_unique_vars(self, input_data_dict, filetype):
        """
        Extract uniquely defined global variables set in the 'fv3_conf' or 'parm'
        files, which is dependent on the UFS-WM user.

        Args:
            input_data_dict (dict): Dictionary for referencing sets of input data 
                                    files being used for given regression test.
                                    
            filetype (str): Declare type of configuration files to search for
                            uniquely defined variables dependent on the 
                            UFS-WM user. Options: 'fv3_conf', 'parm'. 
            
        Return: The unique global variables being called within the filetype 
        (e.g. fv3_conf, parm) of interest.
        
        **TODO** [Optional] Setup a logic to detect the unique variables 
        declared w/in the overall /parm files.
        
        """

        # Extract & partition raw text of config. files in /fv3_conf or /parm.
        fv3_relevant_txt = []
        for (f, txt) in input_data_dict[filetype].items():
            fv3_relevant_txt.append(txt)

        # Extract unique global variables of entire config. files' corpus
        fv3_global_vars = []
        for v in fv3_relevant_txt:
            for txt in v:
                global_vars = []
                txt_bracket = re.findall(r'(?<=\[).+?(?=\])', txt)
                txt_para = re.findall(r'(?<=\{).+?(?=\})', txt)
                if txt_bracket != []:
                    fv3_global_vars.append(txt_bracket)
                if txt_para != []:
                    fv3_global_vars.append(txt_para)
        unique_vars = {x for l in fv3_global_vars for x in l}

        return unique_vars

    def preprocess_fv3(self, input_data_dict):
        """
        Maps source & destination of data files being transfered from on-prem disk to
        experimental directory created by the UFS-WM user as configured within 
        each unique /fv3_conf file.
        
        Args:
            input_data_dict (dict): Dictionary for referencing sets of input data 
                                    files being used for given regression test.
        
        Return (dict): Nested dictionary of source-to-destination paths of data files
        being copied, linked, moved, or synced from paths (excluding "RESTART" paths) to
        the experimental PTMP directory configured within each unique 'fv3_conf' file.
        
        For parent folders for which data files are being sourced & transferred to PTMP,
        directories starting w/ '${FILEDIR}' may copy files from [INPUTDATA_ROOT] 
        Input folder if model is initialized by user with "Warm Start from Initialization 
        Time" via $MODEL_INTIALIZATION = True. Directories starting with '${PATHRT}' are 
        the /tests & /parm folders comprised of /parm raw .txt data files (interpret parm
        scripts?). 

        **TODO: [Confirm] Directory starting w/ '$RFILE' & '../' may not be relevant 
        input data files since, they appear to be associated w/ user's CWD's Restart 
        data files.
        
        **TODO:** [Optional] Merge w/ 'xml-to-json' script to grab data file extensions
                  from xml-to-json' script. 
                  
        """
        
        # Set parent folders for which data files are being sourced & transferred to PTMP. 
        dir_prefix = ['@[INPUTDATA_ROOT_WW3]', 
                      '@[INPUTDATA_ROOT_BMIC]', 
                      '@[INPUTDATA_ROOT]',
                      '${FILEDIR}',
                      '${PATHRT}',
                      '${FV3_IC}',
                      '${MOM_IC}',
                      '${ICE_IC}',
                       '../',
                      '$RFILE']

        # [Optional] If filtering to files residing in the 2021 S3 bucket to determine 
        # files w/ ext in each /tests file.
        #datatype_ext = ['nc', 'grb', 'dat', 'txt', 'diag_table', 'field_table', 'f77',
        #               'expanded_rain_LE', 'DETAMPNEW_DATA_LE', 'TBL', 'jnl',
        #               'diag_table_NAM_phys', 'diag_table_aod', 'diag_table_gfdlmp',
        #               'diag_table_gfsv16', 'diag_table_gfsv16_merra2',
        #               'diag_table_gfsv16_thompson_extdiag', 'diag_table_gocart',
        #               'diag_table_mgrs', 'diag_table_mgtkers', 'diag_table_thompson',
        #               'diag_table_wsm6', 'field_table_NAM_phys', 'field_table_csawmg',
        #               'field_table_csawmgshoc', 'field_table_gfdlmp',
        #               'field_table_gfsv16', 'field_table_mgrs', 'field_table_mgtkers',
        #               'field_table_rasmgshoc', 'field_table_satmedmf',
        #               'field_table_thompson', 'field_table_wsm6', 'nml', 'qr_acr_qg',
        #               'qr_acr_qs', 'diag_table_mp', 'res', '*']

        # Extract source (excluding "RESTART" paths) & destination paths of data files being copied, 
        # linked, moved, or synced from on-prem disk to experimental PTMP directory.
        fv3_conf_dict = {}
        unique_bracket_root_folders = []
        unique_brace_root_folders = []
        unique_nobrace_root_folders = []
        unique_cw_root_folders = []
        for fn, txt_list in input_data_dict.items():
            source_path_list = []
            dest_path_list = []
            for txt in txt_list:

                # Determine data files being copied, linked, moved, or synced 
                # for the given /fv_conf file.
                q = txt.split()
                stamp_bracket = [i for i in q if i.startswith('@[')]
                stamp_brace = [b for b in q if b.startswith('${')]
                stamp_misc = [b for b in q if b.startswith('../')]
                stamp_no_brace = [b for b in q if b.startswith('$')]

                if stamp_bracket != []:
                    t = re.findall(r'(?<=\[).+?(?=\])', stamp_bracket[0])
                    unique_bracket_root_folders.append(t[0])
                if stamp_brace != []:
                    t = re.findall(r'(?<=\{).+?(?=\})', stamp_brace[0])
                    unique_brace_root_folders.append(t[0])
                if stamp_no_brace != []:
                    t = re.findall(r'[^a-zA-Z]+', stamp_no_brace[0])
                    unique_nobrace_root_folders.append(t[0].replace("{", ""))
                if stamp_misc != []:
                    unique_cw_root_folders.append('../')

                # Locate & append any data files which are linked from
                # source to destination & overwriting the destination 
                # files -- if exist.
                if txt.startswith('ln'):  
                    ln_list = []
                    for item in txt.split():
                        ln_list.append(item)
                    
                    # Append linked data file's source path.
                    source_path_list.append(ln_list[2])
                    
                    # Append linked data file's "destination" path.  
                    dest_path_list.append(txt.split()[-1])

                # Locate & append any data files which are synced
                # from source to destination -- if exist.
                elif txt.startswith('rsync'):  
                    rsync_list = []
                    for item in txt.split():
                        rsync_list.append(item)
                    
                    # Append synced data file's source path.  
                    source_path_list.append(rsync_list[2])
                    
                    # Append synced data file's "destination" path.  
                    dest_path_list.append(txt.split()[-1])

                # Locate & append any data files which are 
                # transferred from source to destination -- if exist.
                elif txt.startswith('mv'):  
                    mv_list = []
                    for item in txt.split():
                        mv_list.append(item)

                    # Append moved data file's source path.
                    if mv_list[1].startswith("-"):
                        source_path_list.append(mv_list[2])
                    else: 
                        source_path_list.append(mv_list[1])
                    
                    # Append moved data file's destination path.  
                    dest_path_list.append(txt.split()[-1])
                    
                # Locate & append any data files which are 
                # copied from source to destination.     
                elif txt.startswith('cp'):     
                    
                    # Locate & append data files which are copied from
                    # source to destination.
                    for item in txt.split():
                        if item.startswith(tuple(dir_prefix)): #& item.endswith(tuple(datatype_ext)):
                            
                            # Append copied data file's source paths.  
                            source_path_list.append(item)
                        
                            # [Optional] Extracts all sourced data filenames
                            # being copied to PTMP directory per test file.
                            #source_path_list.append(os.path.basename(item))
                            
                    # Append copied data file's destination paths.       
                    dest_path_list.append(txt.split()[-1])
                    
                else:
                    
                    continue
                    
            # Generate 2nd level map of each data file's source-to-"destination" paths.
            fv3_conf_node2 = defaultdict(list)
            for source_path, dest_path in zip(source_path_list, dest_path_list):
                fv3_conf_node2[source_path].append(dest_path)
            
            # Generate map of each data file's source-to-"destination" paths for each unique 
            # '/fv3_conf' file.
            fv3_conf_dict[fn] = fv3_conf_node2

        # Unique chars surrounding the parent foldernames of the data files
        # being copied, synced, moved, or linked.
        unique_bracket_root_folders = list(set(unique_bracket_root_folders))
        unique_brace_root_folders = list(set(unique_brace_root_folders))
        unique_nobrace_root_folders = list(set(unique_nobrace_root_folders))
        unique_cw_root_folders = list(set(unique_cw_root_folders))
        #print("/nUnique cwd parent folders:/n", unique_cw_root_folders)
        #print("/nUnique bracket parent folders:/n", unique_bracket_root_folders)
        #print("/nUnique brace parent folders:/n", unique_brace_root_folders)
        #print("/nUnique no brace parent folders:/n", unique_nobrace_root_folders)

        return fv3_conf_dict
    
    def preprocess_tests(self, input_data_dict):
        """
        Parses, extracts, & maps variables set within the /tests files to their set values.
        
        Args:
            input_data_dict (dict): Dictionary for referencing sets of
                                    input data files being used per 
                                    regression test.
                                    
        Return (dict): Preprocessed /tests files content.
        
        """
        tests_dict = defaultdict(dict)
        for test_name, txt in input_data_dict.items():
            
            # Initialize dictionary & items list per /tests file.
            items_list = []
            default_method_list = []
            partition_list = []
            items_dict = {}
            
            # Parse & extract relevant config. variables set within '/tests' file.
            tokens = list(filter(None, txt[0].replace('export ', '').split('\n')))
            for var in tokens:
                partition_list.append(var.split("="))
            
            # Map relevant variables set within '/tests' file to their variable values.       
            items_list = [item for item in partition_list if len(item)>1]
            for var, var_val in items_list:
                items_dict[var] = var_val.replace('"', '')
            tests_dict[test_name] = items_dict

            # Extract UFS-WM's 'default_var.sh' methods called by a given '/tests' file.
            for token in partition_list:
                if 'export_' in token[0]:
                    default_method_list.append(token[0])
            tests_dict[test_name]['Test Info'] = default_method_list ####################### Is it 'Test Info'?

        return tests_dict
    
    def get_appsphys2testparams(self, outer_dict, input_data_dict):
        """
        Integrate UFS application-to-physics suite build to regression tests map with 
        their corresponding input data files mentioned in config. files (fv3 filename,
        parm filename), baseline data files mentioned in /tests file's 'CNTL_DIR'
        variable, & additional parameters declared for a given regression test's 
        /tests file.

        Args:
            outer_dict (dict): The reconfigured nested dictionary mapping the 
                               UFS application-to-physics suite build to their 
                               set of applicable set of regression tests. 
                               
            input_data_dict (dict): Dictionary for referencing sets of input data files being 
                                    used per regression test.
            
        Return (dict): Dictionary associating UFS application-to-physics suite builds to
        their regression tests and mapping each test with their required input data files,
        baseline data files, and test parameters.
                
        """
        
        # Incorporate each UFS app's corresponding test parameters, fv3_conf filename, & parm filename.
        joined_test_dict = {}
        for app2phys, val in outer_dict.items():
            for test_type, test_names in val.items():
                outer_dict[app2phys][test_type] = dict.fromkeys(test_names, {})
                for v in test_names:
                     outer_dict[app2phys][test_type][v] = input_data_dict['tests'][v]    
                        
        return outer_dict
    
    def convert_dict2df(self, appsphys2test_dict):
        """
        Convert "appsphys2test_dict" to a dataframe.

        Args:
            appsphys2test_dict (dict): Dictionary associating UFS application-to-physics 
                                       suite builds to their regression tests and mapping 
                                       each test with their required input data files, 
                                       baseline data files, and test parameters.

        Return (pd.DataFrame): Table associating UFS application-to-physics suite builds 
        to their regression tests and mapping each test with their required input data 
        files, baseline data files, and test parameters.

        """
        
        # Generate table from nested dictionary.
        appsphys2test_df = pd.DataFrame.from_records([(node1, node2, node3, leaf, leaf['CNTL_DIR'], leaf['FV3_RUN'])
                                                      for node1, node2_dict in appsphys2test_dict.items()
                                                      for node2, node3_dict in node2_dict.items()
                                                      for node3, leaf in node3_dict.items()],
                                                     columns=['App-to-Phys', 
                                                              'Test Type', 
                                                              'Test Name', 
                                                              'Test Info', 
                                                              'CNTL Folder', 
                                                              'FV3 File'])

        # Append /parm filename if rq'd & set by the given regression test's /test file.
        for idx, v in appsphys2test_df['Test Info'].items():
            if 'INPUT_NML' in v:
                appsphys2test_df.loc[idx, 'Parm File'] = v['INPUT_NML']
        
        # Partition UFS application & physics suite.
        appsphys2test_df[['UFS_App', 'Physics_Suite']] = pd.DataFrame(appsphys2test_df['App-to-Phys'].to_list(), 
                                                                      index=appsphys2test_df.index)
        appsphys2test_df.insert(0, 'UFS_App', appsphys2test_df.pop('UFS_App'))
        appsphys2test_df.insert(1, 'Physics_Suite', appsphys2test_df.pop('Physics_Suite'))
        appsphys2test_df = appsphys2test_df.drop(['App-to-Phys'], axis=1)

        # Save table as a pickle file.      
        self.save2pickle(appsphys2test_df, './ufs_app2files_map/ufs_app2test2data_df')

        return appsphys2test_df

    def save2pickle(self, data2save, fn):
        """
        Save data to a pickle file.
        
        Args:
            data2save (dict, str, tuple, list, pd.DataFrame): Data object to save.
            fn (str): Filename to save data object as a pickle file.. 
        
        Return : None
        
        """
        with open(fn + '.pkl', 'wb') as file:
            pickle.dump(data2save, file)
            
        return
    
    def read_pickle(self, fn):
        """
        Read data from a pickle file.
        
        Args:
            fn (str): Filename of pickle file. 
        
        Return (dict, str, tuple, list, pd.DataFrame): Data object within
        pickle file. 
        
        """
        with open(fn + '.pkl', 'rb') as file:
            data = pickle.load(file)
            
        return data