import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  Button, 
  Grid, 
  TextField, 
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  LinearProgress,
  Alert,
  Tabs,
  Tab
} from '@mui/material';

const ABTestingDashboard = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [experiments, setExperiments] = useState([]);
  const [groundTruthDocs, setGroundTruthDocs] = useState([]);
  const [bestPrompts, setBestPrompts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [openDialog, setOpenDialog] = useState(false);
  const [dialogType, setDialogType] = useState(''); // 'experiment' or 'ground-truth'
  
  // Form states
  const [experimentForm, setExperimentForm] = useState({
    prompt_name: '',
    prompt_version: '',
    prompt_text: '',
    llm_model: 'grok-4-fast-reasoning',
    description: '',
    hypothesis: '',
    is_baseline: false
  });
  
  const [groundTruthForm, setGroundTruthForm] = useState({
    document_name: '',
    original_filename: '',
    town: '',
    county: '',
    state: 'NJ',
    verified_by: '',
    number_of_zones: 1,
    complexity: 'medium'
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // Load experiments
      const experimentsRes = await fetch('/api/ab-testing/experiments');
      if (experimentsRes.ok) {
        const experimentsData = await experimentsRes.json();
        setExperiments(experimentsData.experiments || []);
      }

      // Load ground truth documents  
      const groundTruthRes = await fetch('/api/ab-testing/ground-truth/documents');
      if (groundTruthRes.ok) {
        const groundTruthData = await groundTruthRes.json();
        setGroundTruthDocs(groundTruthData.documents || []);
      }

      // Load best prompts
      const bestPromptsRes = await fetch('/api/ab-testing/results/best-prompts');
      if (bestPromptsRes.ok) {
        const bestPromptsData = await bestPromptsRes.json();
        setBestPrompts(bestPromptsData.best_prompts || []);
      }
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateExperiment = async () => {
    try {
      const response = await fetch('/api/ab-testing/experiments', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(experimentForm),
      });

      if (response.ok) {
        setOpenDialog(false);
        loadData();
        setExperimentForm({
          prompt_name: '',
          prompt_version: '',
          prompt_text: '',
          llm_model: 'grok-4-fast-reasoning',
          description: '',
          hypothesis: '',
          is_baseline: false
        });
      }
    } catch (error) {
      console.error('Error creating experiment:', error);
    }
  };

  const handleCreateGroundTruth = async () => {
    try {
      const response = await fetch('/api/ab-testing/ground-truth/documents', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(groundTruthForm),
      });

      if (response.ok) {
        setOpenDialog(false);
        loadData();
        setGroundTruthForm({
          document_name: '',
          original_filename: '',
          town: '',
          county: '',
          state: 'NJ',
          verified_by: '',
          number_of_zones: 1,
          complexity: 'medium'
        });
      }
    } catch (error) {
      console.error('Error creating ground truth:', error);
    }
  };

  const getAccuracyColor = (accuracy) => {
    if (accuracy >= 0.9) return 'success';
    if (accuracy >= 0.7) return 'warning';
    return 'error';
  };

  const formatAccuracy = (accuracy) => {
    return `${(accuracy * 100).toFixed(1)}%`;
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        🧪 A/B Testing Dashboard
      </Typography>
      
      <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 3 }}>
        Track prompt performance and improve zoning extraction accuracy
      </Typography>

      <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
        <Tab label="Experiments" />
        <Tab label="Ground Truth" />
        <Tab label="Results" />
      </Tabs>

      {/* Experiments Tab */}
      {activeTab === 0 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
            <Typography variant="h5">Prompt Experiments</Typography>
            <Button 
              variant="contained" 
              onClick={() => {
                setDialogType('experiment');
                setOpenDialog(true);
              }}
            >
              Create New Experiment
            </Button>
          </Box>

          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Prompt Name</TableCell>
                  <TableCell>Version</TableCell>
                  <TableCell>Model</TableCell>
                  <TableCell>Tests</TableCell>
                  <TableCell>Accuracy</TableCell>
                  <TableCell>Success Rate</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {experiments.map((exp) => (
                  <TableRow key={exp.id}>
                    <TableCell>{exp.prompt_name}</TableCell>
                    <TableCell>{exp.prompt_version}</TableCell>
                    <TableCell>{exp.llm_model}</TableCell>
                    <TableCell>{exp.total_tests}</TableCell>
                    <TableCell>
                      <Chip 
                        label={formatAccuracy(exp.average_accuracy_score)} 
                        color={getAccuracyColor(exp.average_accuracy_score)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {exp.total_tests > 0 ? formatAccuracy(exp.successful_extractions / exp.total_tests) : 'N/A'}
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={exp.is_active ? 'Active' : 'Inactive'} 
                        color={exp.is_active ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Button 
                        size="small" 
                        onClick={() => {/* Toggle active status */}}
                      >
                        {exp.is_active ? 'Deactivate' : 'Activate'}
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      {/* Ground Truth Tab */}
      {activeTab === 1 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
            <Typography variant="h5">Ground Truth Documents</Typography>
            <Button 
              variant="contained" 
              onClick={() => {
                setDialogType('ground-truth');
                setOpenDialog(true);
              }}
            >
              Add Ground Truth Document
            </Button>
          </Box>

          <Grid container spacing={3}>
            {groundTruthDocs.map((doc) => (
              <Grid item xs={12} md={6} lg={4} key={doc.id}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {doc.document_name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      📍 {doc.town}, {doc.county}, {doc.state}
                    </Typography>
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      🏗️ {doc.number_of_zones} zones
                    </Typography>
                    <Typography variant="body2">
                      📊 Complexity: {doc.complexity}
                    </Typography>
                    <Typography variant="body2">
                      ✅ Verified by: {doc.verified_by}
                    </Typography>
                    <Button 
                      size="small" 
                      sx={{ mt: 2 }}
                      onClick={() => {/* View requirements */}}
                    >
                      View Requirements
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* Results Tab */}
      {activeTab === 2 && (
        <Box>
          <Typography variant="h5" gutterBottom>Best Performing Prompts</Typography>
          
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Prompt</TableCell>
                  <TableCell>Model</TableCell>
                  <TableCell>Tests</TableCell>
                  <TableCell>Overall Accuracy</TableCell>
                  <TableCell>Field Accuracy</TableCell>
                  <TableCell>Zone Accuracy</TableCell>
                  <TableCell>Success Rate</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {bestPrompts.map((prompt, index) => (
                  <TableRow key={index}>
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight="bold">
                          {prompt.prompt_name} v{prompt.prompt_version}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>{prompt.llm_model}</TableCell>
                    <TableCell>{prompt.total_tests}</TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <LinearProgress 
                          variant="determinate" 
                          value={prompt.avg_accuracy * 100}
                          color={getAccuracyColor(prompt.avg_accuracy)}
                          sx={{ width: 60 }}
                        />
                        <Typography variant="body2">
                          {formatAccuracy(prompt.avg_accuracy)}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      {formatAccuracy(prompt.avg_field_accuracy)}
                    </TableCell>
                    <TableCell>
                      {formatAccuracy(prompt.avg_zone_accuracy)}
                    </TableCell>
                    <TableCell>
                      {formatAccuracy(prompt.success_rate)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      {/* Create Experiment Dialog */}
      <Dialog open={openDialog && dialogType === 'experiment'} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create New Prompt Experiment</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Prompt Name"
                value={experimentForm.prompt_name}
                onChange={(e) => setExperimentForm({...experimentForm, prompt_name: e.target.value})}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Version"
                value={experimentForm.prompt_version}
                onChange={(e) => setExperimentForm({...experimentForm, prompt_version: e.target.value})}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={8}
                label="Prompt Text"
                value={experimentForm.prompt_text}
                onChange={(e) => setExperimentForm({...experimentForm, prompt_text: e.target.value})}
                placeholder="Enter the prompt text that will be sent to the LLM..."
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="LLM Model"
                value={experimentForm.llm_model}
                onChange={(e) => setExperimentForm({...experimentForm, llm_model: e.target.value})}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                value={experimentForm.description}
                onChange={(e) => setExperimentForm({...experimentForm, description: e.target.value})}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Hypothesis"
                value={experimentForm.hypothesis}
                onChange={(e) => setExperimentForm({...experimentForm, hypothesis: e.target.value})}
                placeholder="What improvement do you expect from this prompt?"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={handleCreateExperiment} variant="contained">Create Experiment</Button>
        </DialogActions>
      </Dialog>

      {/* Create Ground Truth Dialog */}
      <Dialog open={openDialog && dialogType === 'ground-truth'} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Ground Truth Document</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Document Name"
                value={groundTruthForm.document_name}
                onChange={(e) => setGroundTruthForm({...groundTruthForm, document_name: e.target.value})}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Original Filename"
                value={groundTruthForm.original_filename}
                onChange={(e) => setGroundTruthForm({...groundTruthForm, original_filename: e.target.value})}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Town"
                value={groundTruthForm.town}
                onChange={(e) => setGroundTruthForm({...groundTruthForm, town: e.target.value})}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="County"
                value={groundTruthForm.county}
                onChange={(e) => setGroundTruthForm({...groundTruthForm, county: e.target.value})}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="State"
                value={groundTruthForm.state}
                onChange={(e) => setGroundTruthForm({...groundTruthForm, state: e.target.value})}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Verified By"
                value={groundTruthForm.verified_by}
                onChange={(e) => setGroundTruthForm({...groundTruthForm, verified_by: e.target.value})}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="number"
                label="Number of Zones"
                value={groundTruthForm.number_of_zones}
                onChange={(e) => setGroundTruthForm({...groundTruthForm, number_of_zones: parseInt(e.target.value)})}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={handleCreateGroundTruth} variant="contained">Add Document</Button>
        </DialogActions>
      </Dialog>

      {loading && (
        <Box sx={{ position: 'fixed', top: 0, left: 0, right: 0, zIndex: 9999 }}>
          <LinearProgress />
        </Box>
      )}
    </Box>
  );
};

export default ABTestingDashboard;
