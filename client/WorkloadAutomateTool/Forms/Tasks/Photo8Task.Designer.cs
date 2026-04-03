using System.Windows.Forms;
namespace WorkloadAutomateTool.Forms.Tasks
{
    partial class Photo8Task
    {
        private System.ComponentModel.IContainer components = null;
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code
        private void InitializeComponent()
        {
            this.panelHeader = new System.Windows.Forms.Panel();
            this.lblCustomerName = new System.Windows.Forms.Label();
            this.lblTaskTitle = new System.Windows.Forms.Label();
            this.btnBack = new System.Windows.Forms.Button();
            this.btnLogin = new System.Windows.Forms.Button();
            this.btnLoadTasks = new System.Windows.Forms.Button();
            this.btnSave = new System.Windows.Forms.Button();
            this.btnUploadToServer = new System.Windows.Forms.Button();
            this.lblStatus = new System.Windows.Forms.Label();
            this.label3 = new System.Windows.Forms.Label();
            this.txtImagePath = new System.Windows.Forms.TextBox();
            this.btnSelectFolder = new System.Windows.Forms.Button();
            this.label2 = new System.Windows.Forms.Label();
            this.txtType = new System.Windows.Forms.TextBox();
            this.label6 = new System.Windows.Forms.Label();
            this.txtContractor = new System.Windows.Forms.TextBox();
            this.label4 = new System.Windows.Forms.Label();
            this.txtContractNo = new System.Windows.Forms.TextBox();
            this.label5 = new System.Windows.Forms.Label();
            this.txtSeason = new System.Windows.Forms.TextBox();
            this.label1 = new System.Windows.Forms.Label();
            this.rtbLabel = new System.Windows.Forms.RichTextBox();
            this.label7 = new System.Windows.Forms.Label();
            this.rtbPO = new System.Windows.Forms.RichTextBox();
            this.dataGridView1 = new System.Windows.Forms.DataGridView();
            this.panelHeader.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.dataGridView1)).BeginInit();
            this.SuspendLayout();
            // 
            // panelHeader
            // 
            this.panelHeader.BackColor = System.Drawing.Color.FromArgb(0, 120, 215);
            this.panelHeader.Controls.Add(this.lblCustomerName);
            this.panelHeader.Controls.Add(this.lblTaskTitle);
            this.panelHeader.Controls.Add(this.btnBack);
            this.panelHeader.Dock = System.Windows.Forms.DockStyle.Top;
            this.panelHeader.Location = new System.Drawing.Point(0, 0);
            this.panelHeader.Name = "panelHeader";
            this.panelHeader.Size = new System.Drawing.Size(800, 60);
            this.panelHeader.TabIndex = 0;
            // 
            // lblCustomerName
            // 
            this.lblCustomerName.AutoSize = true;
            this.lblCustomerName.Font = new System.Drawing.Font("Segoe UI", 10F);
            this.lblCustomerName.ForeColor = System.Drawing.Color.White;
            this.lblCustomerName.Location = new System.Drawing.Point(20, 35);
            this.lblCustomerName.Name = "lblCustomerName";
            this.lblCustomerName.Size = new System.Drawing.Size(70, 19);
            this.lblCustomerName.TabIndex = 0;
            this.lblCustomerName.Text = "HADDAD";
            // 
            // lblTaskTitle
            // 
            this.lblTaskTitle.AutoSize = true;
            this.lblTaskTitle.Font = new System.Drawing.Font("Segoe UI", 14F, System.Drawing.FontStyle.Bold);
            this.lblTaskTitle.ForeColor = System.Drawing.Color.White;
            this.lblTaskTitle.Location = new System.Drawing.Point(20, 10);
            this.lblTaskTitle.Name = "lblTaskTitle";
            this.lblTaskTitle.Size = new System.Drawing.Size(150, 25);
            this.lblTaskTitle.TabIndex = 1;
            this.lblTaskTitle.Text = "Photo 8 Upload";
            // 
            // btnBack
            // 
            this.btnBack.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right;
            this.btnBack.BackColor = System.Drawing.Color.FromArgb(220, 53, 69);
            this.btnBack.FlatAppearance.BorderSize = 0;
            this.btnBack.Font = new System.Drawing.Font("Segoe UI", 10F, System.Drawing.FontStyle.Bold);
            this.btnBack.ForeColor = System.Drawing.Color.White;
            this.btnBack.Location = new System.Drawing.Point(710, 15);
            this.btnBack.Name = "btnBack";
            this.btnBack.Size = new System.Drawing.Size(70, 30);
            this.btnBack.TabIndex = 2;
            this.btnBack.Text = "Back";
            this.btnBack.UseVisualStyleBackColor = false;
            this.btnBack.Click += new System.EventHandler(this.BtnBack_Click);
            // 
            // btnLogin
            // 
            this.btnLogin.BackColor = System.Drawing.Color.FromArgb(40, 167, 69);
            this.btnLogin.FlatAppearance.BorderSize = 0;
            this.btnLogin.Font = new System.Drawing.Font("Segoe UI", 10F, System.Drawing.FontStyle.Bold);
            this.btnLogin.ForeColor = System.Drawing.Color.White;
            this.btnLogin.Location = new System.Drawing.Point(15, 70);
            this.btnLogin.Name = "btnLogin";
            this.btnLogin.Size = new System.Drawing.Size(120, 35);
            this.btnLogin.TabIndex = 3;
            this.btnLogin.Text = "Login";
            this.btnLogin.UseVisualStyleBackColor = false;
            this.btnLogin.Click += new System.EventHandler(this.BtnLogin_Click);
            // 
            // btnLoadTasks
            // 
            this.btnLoadTasks.BackColor = System.Drawing.Color.FromArgb(0, 123, 255);
            this.btnLoadTasks.FlatAppearance.BorderSize = 0;
            this.btnLoadTasks.Font = new System.Drawing.Font("Segoe UI", 10F, System.Drawing.FontStyle.Bold);
            this.btnLoadTasks.ForeColor = System.Drawing.Color.White;
            this.btnLoadTasks.Location = new System.Drawing.Point(141, 70);
            this.btnLoadTasks.Name = "btnLoadTasks";
            this.btnLoadTasks.Size = new System.Drawing.Size(120, 35);
            this.btnLoadTasks.TabIndex = 4;
            this.btnLoadTasks.Text = "Load Draft";
            this.btnLoadTasks.UseVisualStyleBackColor = false;
            this.btnLoadTasks.Click += new System.EventHandler(this.BtnLoadTasks_Click);
            // 
            // btnSave
            // 
            this.btnSave.BackColor = System.Drawing.Color.FromArgb(255, 193, 7);
            this.btnSave.FlatAppearance.BorderSize = 0;
            this.btnSave.Font = new System.Drawing.Font("Segoe UI", 10F, System.Drawing.FontStyle.Bold);
            this.btnSave.ForeColor = System.Drawing.Color.Black;
            this.btnSave.Location = new System.Drawing.Point(267, 70);
            this.btnSave.Name = "btnSave";
            this.btnSave.Size = new System.Drawing.Size(120, 35);
            this.btnSave.TabIndex = 5;
            this.btnSave.Text = "Save Draft";
            this.btnSave.UseVisualStyleBackColor = false;
            this.btnSave.Click += new System.EventHandler(this.BtnSave_Click);
            // 
            // btnUploadToServer
            // 
            this.btnUploadToServer.BackColor = System.Drawing.Color.FromArgb(111, 66, 193);
            this.btnUploadToServer.FlatAppearance.BorderSize = 0;
            this.btnUploadToServer.Font = new System.Drawing.Font("Segoe UI", 10F, System.Drawing.FontStyle.Bold);
            this.btnUploadToServer.ForeColor = System.Drawing.Color.White;
            this.btnUploadToServer.Location = new System.Drawing.Point(393, 70);
            this.btnUploadToServer.Name = "btnUploadToServer";
            this.btnUploadToServer.Size = new System.Drawing.Size(150, 35);
            this.btnUploadToServer.TabIndex = 6;
            this.btnUploadToServer.Text = "Upload to Server";
            this.btnUploadToServer.UseVisualStyleBackColor = false;
            this.btnUploadToServer.Click += new System.EventHandler(this.BtnUploadToServer_Click);
            // 
            // lblStatus
            // 
            this.lblStatus.Font = new System.Drawing.Font("Segoe UI", 10F, System.Drawing.FontStyle.Bold);
            this.lblStatus.Location = new System.Drawing.Point(15, 115);
            this.lblStatus.Name = "lblStatus";
            this.lblStatus.Size = new System.Drawing.Size(770, 25);
            this.lblStatus.TabIndex = 7;
            this.lblStatus.Text = "Status: Waiting...";
            this.lblStatus.TextAlign = System.Drawing.ContentAlignment.MiddleCenter;
            // 
            // label3
            // 
            this.label3.AutoSize = true;
            this.label3.Font = new System.Drawing.Font("Microsoft Sans Serif", 10F, System.Drawing.FontStyle.Bold);
            this.label3.Location = new System.Drawing.Point(15, 150);
            this.label3.Name = "label3";
            this.label3.Size = new System.Drawing.Size(102, 17);
            this.label3.TabIndex = 8;
            this.label3.Text = "Image Folder";
            // 
            // txtImagePath
            // 
            this.txtImagePath.Font = new System.Drawing.Font("Microsoft Sans Serif", 10F);
            this.txtImagePath.Location = new System.Drawing.Point(130, 147);
            this.txtImagePath.Name = "txtImagePath";
            this.txtImagePath.Size = new System.Drawing.Size(540, 23);
            this.txtImagePath.TabIndex = 9;
            this.txtImagePath.TextChanged += new System.EventHandler(this.TxtImagePath_TextChanged);
            // 
            // btnSelectFolder
            // 
            this.btnSelectFolder.Font = new System.Drawing.Font("Segoe UI", 9F);
            this.btnSelectFolder.Location = new System.Drawing.Point(676, 146);
            this.btnSelectFolder.Name = "btnSelectFolder";
            this.btnSelectFolder.Size = new System.Drawing.Size(100, 25);
            this.btnSelectFolder.TabIndex = 10;
            this.btnSelectFolder.Text = "Select";
            this.btnSelectFolder.UseVisualStyleBackColor = true;
            this.btnSelectFolder.Click += new System.EventHandler(this.BtnSelectFolder_Click);
            // 
            // label2
            // 
            this.label2.AutoSize = true;
            this.label2.Font = new System.Drawing.Font("Microsoft Sans Serif", 10F, System.Drawing.FontStyle.Bold);
            this.label2.Location = new System.Drawing.Point(15, 185);
            this.label2.Name = "label2";
            this.label2.Size = new System.Drawing.Size(40, 17);
            this.label2.TabIndex = 11;
            this.label2.Text = "Type";
            // 
            // txtType
            // 
            this.txtType.Font = new System.Drawing.Font("Microsoft Sans Serif", 10F);
            this.txtType.Location = new System.Drawing.Point(130, 182);
            this.txtType.Name = "txtType";
            this.txtType.Size = new System.Drawing.Size(200, 23);
            this.txtType.TabIndex = 12;
            this.txtType.TextChanged += new System.EventHandler(this.TxtType_TextChanged);
            // 
            // label6
            // 
            this.label6.AutoSize = true;
            this.label6.Font = new System.Drawing.Font("Microsoft Sans Serif", 10F, System.Drawing.FontStyle.Bold);
            this.label6.Location = new System.Drawing.Point(350, 185);
            this.label6.Name = "label6";
            this.label6.Size = new System.Drawing.Size(84, 17);
            this.label6.TabIndex = 13;
            this.label6.Text = "Contractor";
            // 
            // txtContractor
            // 
            this.txtContractor.Font = new System.Drawing.Font("Microsoft Sans Serif", 10F);
            this.txtContractor.Location = new System.Drawing.Point(450, 182);
            this.txtContractor.Name = "txtContractor";
            this.txtContractor.Size = new System.Drawing.Size(200, 23);
            this.txtContractor.TabIndex = 14;
            this.txtContractor.TextChanged += new System.EventHandler(this.TxtContractor_TextChanged);
            // 
            // label4
            // 
            this.label4.AutoSize = true;
            this.label4.Font = new System.Drawing.Font("Microsoft Sans Serif", 10F, System.Drawing.FontStyle.Bold);
            this.label4.Location = new System.Drawing.Point(15, 220);
            this.label4.Name = "label4";
            this.label4.Size = new System.Drawing.Size(89, 17);
            this.label4.TabIndex = 15;
            this.label4.Text = "ContractNo";
            // 
            // txtContractNo
            // 
            this.txtContractNo.Font = new System.Drawing.Font("Microsoft Sans Serif", 10F);
            this.txtContractNo.Location = new System.Drawing.Point(130, 217);
            this.txtContractNo.Name = "txtContractNo";
            this.txtContractNo.Size = new System.Drawing.Size(200, 23);
            this.txtContractNo.TabIndex = 16;
            // 
            // label5
            // 
            this.label5.AutoSize = true;
            this.label5.Font = new System.Drawing.Font("Microsoft Sans Serif", 10F, System.Drawing.FontStyle.Bold);
            this.label5.Location = new System.Drawing.Point(350, 220);
            this.label5.Name = "label5";
            this.label5.Size = new System.Drawing.Size(62, 17);
            this.label5.TabIndex = 17;
            this.label5.Text = "Season";
            // 
            // txtSeason
            // 
            this.txtSeason.Font = new System.Drawing.Font("Microsoft Sans Serif", 10F);
            this.txtSeason.Location = new System.Drawing.Point(450, 217);
            this.txtSeason.Name = "txtSeason";
            this.txtSeason.Size = new System.Drawing.Size(200, 23);
            this.txtSeason.TabIndex = 18;
            this.txtSeason.TextChanged += new System.EventHandler(this.TxtSeason_TextChanged);
            // 
            // label1
            // 
            this.label1.AutoSize = true;
            this.label1.Font = new System.Drawing.Font("Microsoft Sans Serif", 10F, System.Drawing.FontStyle.Bold);
            this.label1.Location = new System.Drawing.Point(15, 255);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(79, 17);
            this.label1.TabIndex = 19;
            this.label1.Text = "List Label";
            // 
            // rtbLabel
            // 
            this.rtbLabel.Font = new System.Drawing.Font("Microsoft Sans Serif", 10F);
            this.rtbLabel.Location = new System.Drawing.Point(130, 250);
            this.rtbLabel.Name = "rtbLabel";
            this.rtbLabel.Size = new System.Drawing.Size(646, 50);
            this.rtbLabel.TabIndex = 20;
            // 
            // label7
            // 
            this.label7.AutoSize = true;
            this.label7.Font = new System.Drawing.Font("Microsoft Sans Serif", 10F, System.Drawing.FontStyle.Bold);
            this.label7.Location = new System.Drawing.Point(15, 310);
            this.label7.Name = "label7";
            this.label7.Size = new System.Drawing.Size(55, 17);
            this.label7.TabIndex = 21;
            this.label7.Text = "List PO";
            // 
            // rtbPO
            // 
            this.rtbPO.Font = new System.Drawing.Font("Microsoft Sans Serif", 10F);
            this.rtbPO.Location = new System.Drawing.Point(130, 305);
            this.rtbPO.Name = "rtbPO";
            this.rtbPO.Size = new System.Drawing.Size(646, 60);
            this.rtbPO.TabIndex = 22;
            // 
            // dataGridView1
            // 
            this.dataGridView1.ColumnHeadersHeightSizeMode = System.Windows.Forms.DataGridViewColumnHeadersHeightSizeMode.AutoSize;
            this.dataGridView1.Location = new System.Drawing.Point(15, 375);
            this.dataGridView1.Name = "dataGridView1";
            this.dataGridView1.Size = new System.Drawing.Size(770, 150);
            this.dataGridView1.TabIndex = 23;
            // 
            // Photo8Task
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(800, 540);
            this.Controls.Add(this.dataGridView1);
            this.Controls.Add(this.rtbPO);
            this.Controls.Add(this.label7);
            this.Controls.Add(this.rtbLabel);
            this.Controls.Add(this.label1);
            this.Controls.Add(this.txtSeason);
            this.Controls.Add(this.label5);
            this.Controls.Add(this.txtContractNo);
            this.Controls.Add(this.label4);
            this.Controls.Add(this.txtContractor);
            this.Controls.Add(this.label6);
            this.Controls.Add(this.txtType);
            this.Controls.Add(this.label2);
            this.Controls.Add(this.btnSelectFolder);
            this.Controls.Add(this.txtImagePath);
            this.Controls.Add(this.label3);
            this.Controls.Add(this.lblStatus);
            this.Controls.Add(this.btnUploadToServer);
            this.Controls.Add(this.btnSave);
            this.Controls.Add(this.btnLoadTasks);
            this.Controls.Add(this.btnLogin);
            this.Controls.Add(this.panelHeader);
            this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedSingle;
            this.MaximizeBox = false;
            this.Name = "Photo8Task";
            this.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen;
            this.Text = "Photo 8 Task";
            this.FormClosing += new System.Windows.Forms.FormClosingEventHandler(this.Photo8Task_FormClosing);
            this.panelHeader.ResumeLayout(false);
            this.panelHeader.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)(this.dataGridView1)).EndInit();
            this.ResumeLayout(false);
            this.PerformLayout();
        }
        #endregion
        private System.Windows.Forms.Panel panelHeader;
        private System.Windows.Forms.Label lblCustomerName;
        private System.Windows.Forms.Label lblTaskTitle;
        private System.Windows.Forms.Button btnBack;
        private System.Windows.Forms.Button btnLogin;
        private System.Windows.Forms.Button btnLoadTasks;
        private System.Windows.Forms.Button btnSave;
        private System.Windows.Forms.Label lblStatus;
        private System.Windows.Forms.Label label3;
        private System.Windows.Forms.TextBox txtImagePath;
        private System.Windows.Forms.Button btnSelectFolder;
        private System.Windows.Forms.Label label2;
        private System.Windows.Forms.TextBox txtType;
        private System.Windows.Forms.Label label6;
        private System.Windows.Forms.TextBox txtContractor;
        private System.Windows.Forms.Label label4;
        private System.Windows.Forms.TextBox txtContractNo;
        private System.Windows.Forms.Label label5;
        private System.Windows.Forms.TextBox txtSeason;
        private System.Windows.Forms.Label label1;
        private System.Windows.Forms.RichTextBox rtbLabel;
        private System.Windows.Forms.Label label7;
        private System.Windows.Forms.RichTextBox rtbPO;
        private System.Windows.Forms.DataGridView dataGridView1;
        private System.Windows.Forms.Button btnUploadToServer;
    }
}