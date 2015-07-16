from __future__ import division
import datetime, os, sys
import math
from PyQt4 import QtGui, QtCore
import MOSES
from CheckableComboBox import CheckableComboBox

class PiggyBankWithFilter(QtGui.QWidget):
    def __init__(self, user_id, password):
        super(PiggyBankWithFilter, self).__init__()
        self.clip = QtGui.QApplication.clipboard()
        self.user_id, self.password = user_id, password
        self.category_tree = MOSES.getCategoryTree(self.user_id, self.password)
        self.writers_list = MOSES.getWritersList(self.user_id, self.password)
        self.brands = MOSES.getBrandValues(self.user_id, self.password)
        self.createUI()
        self.piggy_bank_data = []
        self.mapEvents()
        self.changePage()
        self.populateBrand()
        self.populateWriters()
        self.populateCategoryFilters()

    def keyPressEvent(self, e):
        """Vindaloo: Found this code online. Go through it and try to improve it."""
        if (e.modifiers() & QtCore.Qt.ControlModifier):
            if e.key() == QtCore.Qt.Key_C: #copy
                current_tab = self.piggybank_tabs.currentIndex()
                if current_tab == 0:
                    if self.piggybank_summary_tables.currentIndex() == 0:
                        table_to_copy = self.piggybank_summary
                    else:
                        table_to_copy = self.piggybank_summary_editor_summary
                else:
                    table_to_copy = self.piggybank
                selected = table_to_copy.selectedRanges()
                s = '\t'+"\t".join([str(table_to_copy.horizontalHeaderItem(i).text()) for i in xrange(selected[0].leftColumn(), selected[0].rightColumn()+1)])
                s = s + '\n'
                for r in xrange(selected[0].topRow(), selected[0].bottomRow()+1):
                    s += str(r+1) + '\t' 
                    for c in xrange(selected[0].leftColumn(), selected[0].rightColumn()+1):
                        try:
                            s += str(table_to_copy.item(r,c).text()) + "\t"
                        except AttributeError:
                            s += "\t"
                    s = s[:-1] + "\n" #eliminate last '\t'
                self.clip.setText(s)

    def createUI(self):
        self.instruction_label = QtGui.QLabel("<b>Select filters from the following:</b>")
        self.filter_text_edit = QtGui.QTextEdit()
        self.writers_filter_box = CheckableComboBox("Writers")
        self.description_types_box = CheckableComboBox("Description Types")
        self.source_types_box = CheckableComboBox("Source")
        self.BUs_filter_box = CheckableComboBox("BUs")
        self.super_categories_filter_box = CheckableComboBox("Super-Categories")
        self.categories_filter_box = CheckableComboBox("Categories")
        self.sub_categories_filter_box = CheckableComboBox("Sub-Categories")
        self.verticals_filter_box = CheckableComboBox("Verticals")
        self.brands_filter_box = CheckableComboBox("Brands")
        self.start_date_edit = QtGui.QDateTimeEdit()
        self.start_date_edit.setDate(QtCore.QDate(datetime.date.today()))
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("MMMM dd, yyyy")
        self.start_date_edit.setMinimumDate(QtCore.QDate(2015,1,1))
        self.start_date_edit.setDate(QtCore.QDate(datetime.date.today()))
        self.end_date_edit = QtGui.QDateTimeEdit()
        self.end_date_edit.setDate(QtCore.QDate(datetime.date.today()))
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("MMMM dd, yyyy")
        self.end_date_edit.setMinimumDate(self.start_date_edit.date().toPyDate())
        self.end_date_edit.setMaximumDate(datetime.date.today())
        self.all_time_dates = QtGui.QCheckBox("Pull All Time Data")
        self.all_time_dates.setToolTip("Check this box to pull data for the selected filter from all available data.")
        self.piggybank = QtGui.QTableWidget(0,0)
        self.piggybank.setStyleSheet("gridline-color: rgb(0, 0, 0)")

        self.piggybank_summary_widget = QtGui.QWidget()
        self.piggybank_summary_column_chooser_label = QtGui.QLabel("Select Column(s):")
        self.piggybank_summary_column_chooser = CheckableComboBox("Columns")
        self.piggybank_summary_column_chooser.addItems(["Writer Name","Source", "Description Type", "BU","Super-Category", "Category", "Sub-Category", "Vertical", "Brand"])
        self.piggybank_summary_refresh_button = QtGui.QPushButton("Refresh Summary Table")
        self.piggybank_summary = QtGui.QTableWidget(0,0)
        self.piggybank_summary.setStyleSheet("gridline-color: rgb(0, 0, 0)")
        self.piggybank_summary_audit_percentage_label = QtGui.QLabel("Audit Percentage:")
        self.piggybank_summary_audit_percentage = QtGui.QSpinBox()
        self.piggybank_summary_audit_percentage.setRange(0,100)
        self.piggybank_summary_audit_percentage.setSuffix("%")
        self.piggybank_summary_editor_utilization = QtGui.QDoubleSpinBox()
        self.piggybank_summary_editors_label = QtGui.QLabel("Editor:")
        self.piggybank_summary_editors_list = QtGui.QComboBox()
        self.resetEditorConstraints()
        editors_list = self.editor_audit_constraints.keys()
        editors_list.sort()
        self.piggybank_summary_editors_list.addItems(editors_list)
        self.piggybank_summary_editors_equality_checkbox = QtGui.QCheckBox("Use Equal Targets For All Editors")
        self.piggybank_summary_editors_equality_checkbox.setCheckState(False)
        self.piggybank_summary_editor_utilization_label = QtGui.QLabel("Editor Utilization:")
        self.piggybank_summary_editor_utilization.setRange(0,3000.0)
        self.piggybank_summary_editor_utilization.setSingleStep(0.05)
        self.piggybank_summary_editor_minimum_wc_label = QtGui.QLabel("Minimum Word Count:")
        self.piggybank_summary_editor_minimum_wc = QtGui.QSpinBox()
        self.piggybank_summary_editor_minimum_wc.setRange(0,5000)
        self.piggybank_summary_editor_minimum_wc.setSingleStep(100)      
        self.piggybank_summary_editor_maximum_wc_label = QtGui.QLabel("Maximum Word Count:")
        self.piggybank_summary_editor_maximum_wc = QtGui.QSpinBox()
        self.piggybank_summary_editor_maximum_wc.setRange(0,5000)
        self.piggybank_summary_editor_maximum_wc.setSingleStep(100)
        self.piggybank_summary_editor_total_wc_label = QtGui.QLabel("Total Word Count (Auto):")
        self.piggybank_summary_editor_total_wc = QtGui.QSpinBox()
        self.piggybank_summary_editor_total_wc.setValue(0)
        self.piggybank_summary_editor_total_wc.setRange(0,3000000)
        self.piggybank_summary_editor_total_wc.setEnabled(False)
        self.piggybank_summary_reset_stats = QtGui.QPushButton("Reset Editor Stats")
        self.piggybank_summary_editor_summary = QtGui.QTableWidget(0,0)

        self.piggybank_summary_tables = QtGui.QTabWidget()
        self.piggybank_summary_tables.addTab(self.piggybank_summary,"Audit Break Up")
        self.piggybank_summary_tables.addTab(self.piggybank_summary_editor_summary, "Editor Summary")

        
        self.piggybank_summary_layout = QtGui.QGridLayout()
        self.piggybank_summary_layout.addWidget(self.piggybank_summary_column_chooser_label,0,0)
        self.piggybank_summary_layout.addWidget(self.piggybank_summary_column_chooser,0,1)
        self.piggybank_summary_layout.addWidget(self.piggybank_summary_editors_equality_checkbox,0,2)
        self.piggybank_summary_layout.addWidget(self.piggybank_summary_refresh_button,0,3)
        self.piggybank_summary_layout.addWidget(self.piggybank_summary_reset_stats,0,4)
        self.piggybank_summary_layout.addWidget(self.piggybank_summary_editors_label,1,0)
        self.piggybank_summary_layout.addWidget(self.piggybank_summary_editors_list,1,1)
        self.piggybank_summary_layout.addWidget(self.piggybank_summary_audit_percentage_label,1,2)
        self.piggybank_summary_layout.addWidget(self.piggybank_summary_audit_percentage,1,3)
        self.piggybank_summary_layout.addWidget(self.piggybank_summary_editor_utilization_label,1,4)
        self.piggybank_summary_layout.addWidget(self.piggybank_summary_editor_utilization,1,5)
        self.piggybank_summary_layout.addWidget(self.piggybank_summary_editor_minimum_wc_label,2,0)
        self.piggybank_summary_layout.addWidget(self.piggybank_summary_editor_minimum_wc,2,1)
        self.piggybank_summary_layout.addWidget(self.piggybank_summary_editor_maximum_wc_label,2,2)
        self.piggybank_summary_layout.addWidget(self.piggybank_summary_editor_maximum_wc,2,3)
        self.piggybank_summary_layout.addWidget(self.piggybank_summary_editor_total_wc_label,2,4)
        self.piggybank_summary_layout.addWidget(self.piggybank_summary_editor_total_wc,2,5)
        self.piggybank_summary_layout.addWidget(self.piggybank_summary_tables,3,0,8,8)
        self.piggybank_summary_widget.setLayout(self.piggybank_summary_layout)
        
        self.piggybank_tabs = QtGui.QTabWidget()
        self.piggybank_tabs.addTab(self.piggybank_summary_widget,"Audit Planner")
        self.piggybank_tabs.addTab(self.piggybank,"Piggy Bank")
        
        self.reset_button = QtGui.QPushButton("Reset Visible Data")
        self.reset_button.setMinimumWidth(120)
        self.reset_button.setMinimumHeight(20)
        reset_style_string = """
            .QPushButton {
                background-color: red;
                color: white;
                font: 8pt;
            }
            .QPushButton:hover {
                background-color: black;
                color: red;
                font: bold 8pt;
            }
            """
        self.reset_button.setStyleSheet(reset_style_string)
        self.pull_button = QtGui.QPushButton("Pull Data")
        self.pull_button.setToolTip("Click here to extract data from the OINK server for the selected filters.")
        self.pull_button.setMinimumWidth(150)
        self.pull_button.setMinimumHeight(30)
        style_string = """
        .QPushButton {
            background-color: #0088D6;
            color: #FDDE2E;
            font: 12pt;
        }
        .QPushButton:hover {
            background-color: #FDDE2E;
            color: #0088D6;
            font: bold 12pt;
        }
        """
        self.pull_button.setStyleSheet(style_string)
        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.instruction_label)
        filters_sub_layouts = [QtGui.QHBoxLayout() for i in range(4)]
        filters_sub_layouts[0].addWidget(self.all_time_dates,0)
        filters_sub_layouts[0].addWidget(self.start_date_edit,0)
        filters_sub_layouts[0].addWidget(self.end_date_edit,0)
        filters_sub_layouts[0].addWidget(self.writers_filter_box,0)
        filters_sub_layouts[1].addWidget(self.description_types_box,0)
        filters_sub_layouts[1].addWidget(self.source_types_box,0)
        filters_sub_layouts[1].addWidget(self.BUs_filter_box,0)
        filters_sub_layouts[1].addWidget(self.super_categories_filter_box,0)
        filters_sub_layouts[2].addWidget(self.categories_filter_box,0)
        filters_sub_layouts[2].addWidget(self.sub_categories_filter_box,0)
        filters_sub_layouts[2].addWidget(self.verticals_filter_box,0)
        filters_sub_layouts[3].addWidget(self.brands_filter_box,0)
        filters_sub_layouts[3].addWidget(self.reset_button,1)
        filters_sub_layouts[3].addWidget(self.pull_button,2)
        for layout in filters_sub_layouts:
            self.layout.addLayout(layout)
        self.layout.addWidget(self.piggybank_tabs)
        self.setLayout(self.layout)
        self.setWindowTitle("Piggy Bank and Audit Planner")
        if "OINKModules" in os.getcwd():
            icon_file_name_path = os.path.join(os.path.join('..',"Images"),'PORK_Icon.png')
        else:
            icon_file_name_path = os.path.join('Images','PORK_Icon.png')
        self.setWindowIcon(QtGui.QIcon(icon_file_name_path))
        self.move(120,100)

    def mapEvents(self):
        self.start_date_edit.dateChanged.connect(self.limitEndDate)
        self.end_date_edit.dateChanged.connect(self.changeEndDate)
        self.all_time_dates.stateChanged.connect(self.toggleDates)
        self.pull_button.clicked.connect(self.pullData)
        self.piggybank_summary_refresh_button.clicked.connect(self.summarize)
        self.piggybank_summary_editors_equality_checkbox.stateChanged.connect(self.toggleEditorEquality)
        self.piggybank_summary_editors_list.currentIndexChanged.connect(self.changePage)
        self.piggybank_summary_editor_utilization.valueChanged.connect(self.changeUtilization)
        self.piggybank_summary_audit_percentage.valueChanged.connect(self.changeAuditPercentage)
        self.piggybank_summary_editor_maximum_wc.valueChanged.connect(self.changeMaxWordCount)
        self.piggybank_summary_editor_minimum_wc.valueChanged.connect(self.changeMinWordCount)
        self.piggybank_summary_reset_stats.clicked.connect(self.summaryFormReset)

    def changeUtilization(self):
        current_page = str(self.piggybank_summary_editors_list.currentText())
        self.editor_audit_constraints[current_page]["Editor Utilization"] = self.piggybank_summary_editor_utilization.value()

    def changeAuditPercentage(self):
        current_page = str(self.piggybank_summary_editors_list.currentText())
        self.editor_audit_constraints[current_page]["Audit Percentage"] = self.piggybank_summary_audit_percentage.value()
        
    def changeMaxWordCount(self):
        new_word_count = self.piggybank_summary_editor_maximum_wc.value()
        self.piggybank_summary_editor_minimum_wc.setMaximum((new_word_count-1000))
        current_page = str(self.piggybank_summary_editors_list.currentText())
        self.editor_audit_constraints[current_page]["Maximum Word Count"] = new_word_count

    def changeMinWordCount(self):
        new_word_count = self.piggybank_summary_editor_minimum_wc.value()
        self.piggybank_summary_editor_maximum_wc.setMinimum((new_word_count+1000))
        current_page = str(self.piggybank_summary_editors_list.currentText())
        self.editor_audit_constraints[current_page]["Minimum Word Count"] = new_word_count


    def changePage(self):
        current_page = str(self.piggybank_summary_editors_list.currentText())
        self.piggybank_summary_audit_percentage.setValue(self.editor_audit_constraints[current_page]["Audit Percentage"])
        self.piggybank_summary_editor_utilization.setValue(self.editor_audit_constraints[current_page]["Editor Utilization"])
        self.piggybank_summary_editor_minimum_wc.setValue(self.editor_audit_constraints[current_page]["Minimum Word Count"])
        self.piggybank_summary_editor_maximum_wc.setValue(self.editor_audit_constraints[current_page]["Maximum Word Count"])
        self.piggybank_summary_editor_total_wc.setValue(self.editor_audit_constraints[current_page]["Total Word Count"])

    def limitEndDate(self):
        self.end_date_edit.setMinimumDate(self.start_date_edit.date())
        self.end_date_edit.setDate(self.start_date_edit.date())
        self.populateWriters()
        self.resetEditorConstraints()
        self.changePage()

    def changeEndDate(self):
        self.resetEditorConstraints()
        self.changePage()

    def toggleDates(self,state):
        if state == 0:
            self.start_date_edit.setEnabled(True)
            self.end_date_edit.setEnabled(True)
        else:
            self.start_date_edit.setEnabled(False)
            self.end_date_edit.setEnabled(False)
    
    def toggleEditorEquality(self, state):
        if state == 0:
            self.piggybank_summary_editors_list.setEnabled(True)
        else:
            self.piggybank_summary_editors_list.setEnabled(False)
            self.piggybank_summary_editors_list.setCurrentIndex(self.piggybank_summary_editors_list.findText("All"))

    def populateCategoryFilters(self):
        """This method:
        1. First checks the current filters in the following order BU> Super-Category > Category > Sub-Category > Vertical
        2. If a BU is selected:
            1. It'll populate the Super-Category with the corresponding value(s).
        It should go on and do this for all selected parameters."""
        self.populateBU()
        self.populateSuperCategory()
        self.populateCategory()
        self.populateSubCategory()
        self.populateVertical()

    def populateBU(self):
        self.BUs_filter_box.clear()
        bus = list(set(self.category_tree["BU"]))
        bus.sort()
        self.BUs_filter_box.addItems(bus)

    def populateWriters(self):
        self.writers_filter_box.clear()
        start_date = self.start_date_edit.date().toPyDate()
        end_date = self.end_date_edit.date().toPyDate()
        writers = []
        for writer in self.writers_list:
            if writer["DOJ"] <= end_date:
                if writer["DOL"] is not None:
                    if writer["DOL"] >= start_date:
                        writers.append(writer["Name"])
                else:
                    writers.append(writer["Name"])
        writers.sort()
        self.writers_filter_box.addItems(writers)

    def populateBrand(self):
        self.brands_filter_box.clear()
        self.brands_filter_box.addItems(self.brands)

    def populateSuperCategory(self):
        self.super_categories_filter_box.clear()
        super_categories = list(set(self.category_tree["Super-Category"]))
        super_categories.sort()
        self.super_categories_filter_box.addItems(super_categories)

    def populateSubCategory(self):
        self.sub_categories_filter_box.clear()
        sub_categories = list(set(self.category_tree["Sub-Category"]))
        sub_categories.sort()
        self.sub_categories_filter_box.addItems(sub_categories)

    def populateCategory(self):
        self.categories_filter_box.clear()
        categories = list(set(self.category_tree["Category"]))
        categories.sort()
        self.categories_filter_box.addItems(categories)
    
    def populateVertical(self):
        self.verticals_filter_box.clear()
        verticals = list(set(self.category_tree["Vertical"]))
        verticals.sort()
        self.verticals_filter_box.addItems(verticals)

    def pullData(self):
        #print "Pulling data!"
        filters = self.getFilters()
        data = MOSES.getPiggyBankFiltered(self.user_id, self.password, filters)
        #print len(data)
        piggy_bank_keys = MOSES.getPiggyBankKeys()
        self.piggybank.setRowCount(0)
        self.piggybank.setColumnCount(len(piggy_bank_keys))
        row_index = 0
        for row in data:
            if len(row) > 0:
                self.piggybank.insertRow(row_index)
                column_index = 0
                for key in piggy_bank_keys:
                    self.piggybank.setItem(row_index, column_index, QtGui.QTableWidgetItem(str(row[key])))
                    column_index += 1
                row_index += 1
        self.piggybank.setHorizontalHeaderLabels(piggy_bank_keys)
        #populate the summary next.
        self.piggy_bank_data = data
        self.alertMessage("Completed Pulling PiggyBank","Completed Pulling Piggy Bank between %s and %s."%(self.start_date_edit.date().toPyDate(), self.end_date_edit.date().toPyDate()))

        self.summarize()

    def getSummarizeParameters(self):
        summarize_parameters = self.piggybank_summary_column_chooser.getCheckedItems()
        if summarize_parameters == []:
            summarize_parameters = ["Writer Name","Category","Description Type"]
        return summarize_parameters

    def getBreakUpTableFromPiggyBank(self):
        data = self.piggy_bank_data
        summarize_parameters = self.getSummarizeParameters()
        #Build a summary matrix with the different types of the selected summarize parameters.
        matrix = []
        for row in data:
            row_qualifier = dict((key,None) for key in summarize_parameters)
            for key in summarize_parameters:
                row_qualifier[key] = row[key]
            matrix.append(row_qualifier)
        #Build a dictionary which the values for the selected summarize parameters.
        result = [dict(tupleized) for tupleized in set(tuple(item.items()) for item in matrix)]
        return result, summarize_parameters


    def summarize(self):
        result, summarize_parameters = self.getBreakUpTableFromPiggyBank()
        #Now process for audit percentages
        #First, check if you're looking at this at a writer level
        #If writer level, check if all editors' efficiency is equalized.
        #If the following are satisfied, use overall stats, not the editors' values.
        equalize_editors = True
        if "Writer Name" in summarize_parameters:
            if not self.piggybank_summary_editors_equality_checkbox.isChecked():
                equalize_editors = False
                summarize_parameters.append("Editor Name")

        #Set a bool to check the audit conditions.
        audit_conditions_satisfied = False

        #Now calculate the upper and lower limits based on the utilization and min/max word counts.
        for editor in self.editor_audit_constraints.keys():
            editor_data = self.editor_audit_constraints[editor]
            editor_data["Audit Conditions Satisfied"] = False
            editor_data["Target Maximum Word Count"] = editor_data["Editor Utilization"]*editor_data["Maximum Word Count"]
            editor_data["Target Minimum Word Count"] = editor_data["Editor Utilization"]*editor_data["Minimum Word Count"]
    
        #Now, for as long as the audit conditions aren't satisfied, keep repeating the following steps.
        first_run = True
        while not audit_conditions_satisfied:
            for editor in self.editor_audit_constraints.keys():
                if not self.editor_audit_constraints[editor]["Audit Conditions Satisfied"]:
                    self.editor_audit_constraints[editor]["Total Word Count"] = 0
                    self.editor_audit_constraints[editor]["Audit Count"] = 0
                    #print "Resetting %s's word count." %editor

            #For each row in the result, count the numbers from the piggy bank data set.
            for qualifier_row in result:
                if first_run:
                    qualifier_row["Article Count"] = 0
                    qualifier_row["Word Count"] = 0
                    for row in self.piggy_bank_data:
                        row_match = True
                        for key in qualifier_row:
                            if (key not in ["Article Count", "Word Count", "Suggested Audits","Approx. Word Count of Audits"]):
                                if qualifier_row[key] != row[key]:
                                    row_match = False
                        if row_match:
                            qualifier_row["Article Count"] += 1
                            qualifier_row["Word Count"] += row["Word Count"]
                #Now, plan the suggested audits.
                #If the editors have equalized targets.
                if equalize_editors:
                    audit_percentage = self.editor_audit_constraints["All"]["Audit Percentage"]/100
                    qualifier_row["Suggested Audits"] = int(math.ceil(audit_percentage*qualifier_row["Article Count"]))
                    self.editor_audit_constraints["All"]["Audit Count"] += qualifier_row["Suggested Audits"]
                    qualifier_row["Approx. Word Count of Audits"] = int(math.ceil(qualifier_row["Suggested Audits"]*qualifier_row["Word Count"]/qualifier_row["Article Count"]))
                    self.editor_audit_constraints["All"]["Total Word Count"] += qualifier_row["Approx. Word Count of Audits"]
                else:
                    editor_name = self.getEditorName(qualifier_row["Writer Name"])
                    if not self.editor_audit_constraints[editor_name]["Audit Conditions Satisfied"]:
                        qualifier_row["Editor Name"] = editor_name
                        audit_percentage = self.editor_audit_constraints[editor_name]["Audit Percentage"]/100
                        qualifier_row["Suggested Audits"] = int(math.ceil(audit_percentage*qualifier_row["Article Count"]))
                        self.editor_audit_constraints[editor_name]["Audit Count"] += qualifier_row["Suggested Audits"]
                        qualifier_row["Approx. Word Count of Audits"] = int(math.ceil(qualifier_row["Suggested Audits"]*qualifier_row["Word Count"]/qualifier_row["Article Count"]))
                        self.editor_audit_constraints[editor_name]["Total Word Count"] += qualifier_row["Approx. Word Count of Audits"]

            #Check if the audit conditions have been satisfied.
            if equalize_editors:
                scope = "All"
                if self.editor_audit_constraints[scope]["Total Word Count"] <= self.editor_audit_constraints[scope]["Target Minimum Word Count"]:
                    #print "Under-utilizing %s!" %scope
                    #print """Target Max and Min WCs : %(Target Maximum Word Count)d, %(Target Minimum Word Count)d. Total WC: %(Total Word Count)d""" %(self.editor_audit_constraints[scope])
                    self.editor_audit_constraints[scope]["Audit Percentage"] += self.piggybank_summary_audit_percentage.singleStep()
                    if self.editor_audit_constraints[scope]["Audit Percentage"] > 100:
                        raise Exception
                    #else:
                        #print "Increasing audit percentage to", self.editor_audit_constraints[scope]["Audit Percentage"]
                elif self.editor_audit_constraints[scope]["Total Word Count"] >= self.editor_audit_constraints[scope]["Target Maximum Word Count"]:
                    #Editors are over-utilized
                    #print "Over-utilizing %s!" %scope
                    #print """Target Max and Min WCs : %(Target Maximum Word Count)d, %(Target Minimum Word Count)d. Total WC: %(Total Word Count)d""" %(self.editor_audit_constraints[scope])
                    self.editor_audit_constraints[scope]["Audit Percentage"] -= self.piggybank_summary_audit_percentage.singleStep()
                    if self.editor_audit_constraints[scope]["Audit Percentage"] <= 0:
                        raise Exception
                    #else:
                        #print "Decreasing audit percentage to", self.editor_audit_constraints[scope]["Audit Percentage"]
                elif (self.editor_audit_constraints[scope]["Total Word Count"] >= self.editor_audit_constraints[scope]["Target Minimum Word Count"]) and (self.editor_audit_constraints[scope]["Total Word Count"] <= self.editor_audit_constraints[scope]["Target Maximum Word Count"]):
                    #print "%s is well used.!" %scope
                    if self.editor_audit_constraints[scope]["Audit Percentage"] < 0:
                        raise Exception
                    #print """Target Max and Min WCs : %(Target Maximum Word Count)d, %(Target Minimum Word Count)d. Total WC: %(Total Word Count)d""" %(self.editor_audit_constraints[scope])
                    self.editor_audit_constraints[scope]["Audit Conditions Satisfied"] = True
                else:
                    raise Exception
                audit_conditions_satisfied = self.editor_audit_constraints[editor]["Audit Conditions Satisfied"] and audit_conditions_satisfied
            else:
                editors = self.editor_audit_constraints.keys()
                editors.remove("All")
                editors.sort()
                audit_conditions_satisfied = True
                for editor in editors:
                    scope = editor
                        #Editors are under-utilized
                    if self.editor_audit_constraints[scope]["Total Word Count"] <= self.editor_audit_constraints[scope]["Target Minimum Word Count"]:
                        #print "Under-utilizing %s!" %scope
                        #print """Target Max and Min WCs : %(Target Maximum Word Count)d, %(Target Minimum Word Count)d. Total WC: %(Total Word Count)d""" %(self.editor_audit_constraints[scope])
                        if self.editor_audit_constraints[scope]["Audit Percentage"] >= 100:
                            self.alertMessage("Error Planning Audits","%s's audit percentage is out of bounds. Set to %d%%" %(scope,self.editor_audit_constraints[scope]["Audit Percentage"]))
                            self.editor_audit_constraints[scope]["Audit Conditions Satisfied"] = True
                        else:
                            #print "Increasing audit percentage to", self.editor_audit_constraints[scope]["Audit Percentage"]
                            self.editor_audit_constraints[scope]["Audit Percentage"] += self.piggybank_summary_audit_percentage.singleStep()
                    elif self.editor_audit_constraints[scope]["Total Word Count"] >= self.editor_audit_constraints[scope]["Target Maximum Word Count"]:
                        #Editors are over-utilized
                        #print "Over-utilizing %s!" %scope
                        #print """Target Max and Min WCs : %(Target Maximum Word Count)d, %(Target Minimum Word Count)d. Total WC: %(Total Word Count)d""" %(self.editor_audit_constraints[scope])
                        if self.editor_audit_constraints[scope]["Audit Percentage"] <= 1:
                            self.alertMessage("Error Planning Audits","%s's audit percentage is out of bounds. Set to %d%%" %(scope,self.editor_audit_constraints[scope]["Audit Percentage"]))
                            self.editor_audit_constraints[scope]["Audit Conditions Satisfied"] = True
                        else:
                            #print "Decreasing audit percentage to", self.editor_audit_constraints[scope]["Audit Percentage"]
                            self.editor_audit_constraints[scope]["Audit Percentage"] -= self.piggybank_summary_audit_percentage.singleStep()
                    elif (self.editor_audit_constraints[scope]["Total Word Count"] >= self.editor_audit_constraints[scope]["Target Minimum Word Count"]) and (self.editor_audit_constraints[scope]["Total Word Count"] <= self.editor_audit_constraints[scope]["Target Maximum Word Count"]):
                        #print "%s is well used.!" %scope
                        if self.editor_audit_constraints[scope]["Audit Percentage"] < 0:
                            self.alertMessage("Error Planning Audits","%s's audit percentage is out of bounds. Set to %d%%" %(scope,self.editor_audit_constraints[scope]["Audit Percentage"]))
                            raise Exception
                        #print """Target Max and Min WCs : %(Target Maximum Word Count)d, %(Target Minimum Word Count)d. Total WC: %(Total Word Count)d""" %(self.editor_audit_constraints[scope])
                        self.editor_audit_constraints[scope]["Audit Conditions Satisfied"] = True
                    else:
                        raise Exception
                    audit_conditions_satisfied = self.editor_audit_constraints[editor]["Audit Conditions Satisfied"] and audit_conditions_satisfied
            first_run = False
        headers = summarize_parameters + ["Article Count", "Word Count", "Suggested Audits","Approx. Word Count of Audits"]
        self.piggybank_summary.setRowCount(len(result))
        self.piggybank_summary.setColumnCount(len(headers))
        row_index = 0
        self.piggybank_summary.setSortingEnabled(False)
        for qualifier_row in result:
            column_index = 0
            for key in headers:
                self.piggybank_summary.setItem(row_index, column_index, QtGui.QTableWidgetItem(str(qualifier_row[key])))
                column_index += 1
            row_index += 1
        self.piggybank_summary.setSortingEnabled(True)
        self.piggybank_summary.setHorizontalHeaderLabels(headers)
        self.piggybank_summary.resizeColumnsToContents()
        self.piggybank_summary.resizeRowsToContents()
        
        self.piggybank_summary_editor_summary.setSortingEnabled(False)
        editors = self.editor_audit_constraints.keys()
        editors.remove("All")
        editors.sort()
        row_index = 0
        self.piggybank_summary_editor_summary.setRowCount(3)
        editor_summary_labels = ["Editor Name", "Audit Count", "Total Word Count", "Target Minimum Word Count", "Target Maximum Word Count", "Audit Percentage"]
        self.piggybank_summary_editor_summary.setColumnCount(len(editor_summary_labels))
        for editor in editors:
            self.piggybank_summary_editor_summary.setItem(row_index,0,QtGui.QTableWidgetItem(editor))
            self.piggybank_summary_editor_summary.setItem(row_index,1,QtGui.QTableWidgetItem(str(self.editor_audit_constraints[editor]["Audit Count"])))
            self.piggybank_summary_editor_summary.setItem(row_index,2,QtGui.QTableWidgetItem(str(self.editor_audit_constraints[editor]["Total Word Count"])))
            self.piggybank_summary_editor_summary.setItem(row_index,3,QtGui.QTableWidgetItem(str(self.editor_audit_constraints[editor]["Target Minimum Word Count"])))
            self.piggybank_summary_editor_summary.setItem(row_index,4,QtGui.QTableWidgetItem(str(self.editor_audit_constraints[editor]["Target Maximum Word Count"])))
            self.piggybank_summary_editor_summary.setItem(row_index,5,QtGui.QTableWidgetItem(str(self.editor_audit_constraints[editor]["Audit Percentage"])))
            row_index +=1
        self.piggybank_summary_editor_summary.setSortingEnabled(True)
        self.piggybank_summary_editor_summary.setHorizontalHeaderLabels(editor_summary_labels)
        self.piggybank_summary_editor_summary.resizeColumnsToContents()
        self.piggybank_summary_editor_summary.resizeRowsToContents()

        self.alertMessage("Completed Audit Plan","Completed Audit Plan for %s"%self.start_date_edit.date().toPyDate())
    def getEditorName(self, writer_name):
        editors = [name for name in self.editor_audit_constraints.keys()]
        editors.remove("All")
        for editor in editors:
            if writer_name in self.editor_audit_constraints[editor]["Writers"]:
                return editor

    def getFilters(self):
        return {
            "Start Date": self.start_date_edit.date().toPyDate(),
            "End Date": self.end_date_edit.date().toPyDate(),
            "All Dates": self.all_time_dates.isChecked()
        }

    def summaryFormReset(self):
        self.resetEditorConstraints()
        self.changePage()

    def resetEditorConstraints(self):
        self.editor_audit_constraints = {
        "Varkey": {
            "Audit Percentage":30, 
            "Minimum Word Count": 4000, 
            "Maximum Word Count": 5000,
            "Editor Utilization": 1.0*len(MOSES.getWorkingDatesBetween(self.user_id,self.password,self.start_date_edit.date().toPyDate(),self.end_date_edit.date().toPyDate(),mode="All")),
            "Target Minimum Word Count": 0,
            "Target Maximum Word Count": 0,
            "Total Word Count": 0,
            "Audit Count": 0,
            "Audit Conditions Satisfied": False,
            "Writers": MOSES.getWritersListForEditor(self.user_id, self.password, "Varkey")
            },
        "Varun Chhabria": {
            "Audit Percentage":30, 
            "Minimum Word Count": 2000, 
            "Maximum Word Count": 5000,
            "Editor Utilization": 1.0*len(MOSES.getWorkingDatesBetween(self.user_id,self.password,self.start_date_edit.date().toPyDate(),self.end_date_edit.date().toPyDate(),mode="All")),
            "Target Minimum Word Count": 0,
            "Target Maximum Word Count": 0,
            "Total Word Count": 0,
            "Audit Count": 0,
            "Audit Conditions Satisfied": False,
            "Writers": MOSES.getWritersListForEditor(self.user_id, self.password, "Varun Chhabria")
            },
        "Manasa Prabhu": {
            "Audit Percentage":30, 
            "Minimum Word Count": 4000, 
            "Maximum Word Count": 5000,
            "Editor Utilization": 1.0*len(MOSES.getWorkingDatesBetween(self.user_id,self.password,self.start_date_edit.date().toPyDate(),self.end_date_edit.date().toPyDate(),mode="All")),
            "Target Minimum Word Count": 0,
            "Target Maximum Word Count": 0,
            "Total Word Count": 0,
            "Audit Count": 0,
            "Audit Conditions Satisfied": False,
            "Writers": MOSES.getWritersListForEditor(self.user_id, self.password, "Manasa Prabhu")
            },
        "All": {
            "Audit Percentage":30, 
            "Minimum Word Count": 4000, 
            "Maximum Word Count": 5000,
            "Editor Utilization": 3.0*len(MOSES.getWorkingDatesBetween(self.user_id,self.password,self.start_date_edit.date().toPyDate(),self.end_date_edit.date().toPyDate(),mode="All")),
            "Target Minimum Word Count": 0,
            "Target Maximum Word Count": 0,
            "Total Word Count": 0,
            "Audit Count": 0,
            "Audit Conditions Satisfied": False,
            "Writers": MOSES.getWritersListForEditor(self.user_id, self.password)
            }
        }
    def alertMessage(self, title, message):
        """Vindaloo."""
        QtGui.QMessageBox.about(self, title, message)

if __name__ == "__main__":
    app = QtGui.QApplication([])
    QtGui.qApp.setStyle(QtCore.QString(u'Plastique'))
    u, p = MOSES.getBigbrotherCredentials()
    piggybank = PiggyBankWithFilter(u,p)
    piggybank.show()
    sys.exit(app.exec_())