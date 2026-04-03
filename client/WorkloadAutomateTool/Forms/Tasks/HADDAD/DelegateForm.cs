using System;
using System.Windows.Forms;

namespace WorkloadAutomateTool.Forms.Tasks.HADDAD
{
    public partial class DelegateForm : Form
    {
        public DelegateForm()
        {
            InitializeComponent();
        }

        private void btnOpenPhoto8_Click(object sender, EventArgs e)
        {
            var f1 = new Photo8Form();
            f1.FormClosed += (_, __) => this.Show();
            f1.Show();
            this.Hide();
        }

        private void btnOpenPdfToExcel_Click(object sender, EventArgs e)
        {
            var f2 = new PDFToExcelForm();
            f2.FormClosed += (_, __) => this.Show();
            f2.Show();
            this.Hide();
        }

        private void btnOpenCostingSheet_Click(object sender, EventArgs e)
        {
            var f3 = new CostingForm();
            f3.FormClosed += (_, __) => this.Show();
            f3.Show();
            this.Hide();
        }

        private void btnBack_Click(object sender, EventArgs e)
        {
            this.Close();
        }
    }
}
