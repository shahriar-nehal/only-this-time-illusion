package com.example.locationapplication;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.util.Log;
import android.widget.Button;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

public class MainActivity extends AppCompatActivity {

    private static final String TAG = "LocationResearch";
    private static final int PERMISSION_REQUEST_CODE = 1001;

    private Button startButton;
    private TextView trackingStatus;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        startButton = findViewById(R.id.startWorkoutBtn);
        trackingStatus = findViewById(R.id.trackingStatus);

        startButton.setOnClickListener(v -> requestLocationPermission());
    }

    private void requestLocationPermission() {
        // Request both fine and coarse location (dangerous permissions)
        String[] permissions = new String[]{
                Manifest.permission.ACCESS_FINE_LOCATION,
                Manifest.permission.ACCESS_COARSE_LOCATION
        };
        ActivityCompat.requestPermissions(this, permissions, PERMISSION_REQUEST_CODE);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions,
                                           @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PERMISSION_REQUEST_CODE) {
            // Check if all requested permissions were granted
            boolean allGranted = true;
            for (int result : grantResults) {
                if (result != PackageManager.PERMISSION_GRANTED) {
                    allGranted = false;
                    break;
                }
            }
            if (allGranted) {
                // Permission granted → start service and update UI
                startResearchService();
                startButton.setVisibility(Button.GONE);
                trackingStatus.setText("✓ Tracking started");
                trackingStatus.setVisibility(TextView.VISIBLE);
                Log.d(TAG, "Permission granted, service started.");
            } else {
                // Permission denied → show message, keep button visible
                trackingStatus.setText("❌ Location permission denied. Cannot track.");
                trackingStatus.setVisibility(TextView.VISIBLE);
                Log.d(TAG, "Permission denied.");
            }
        }
    }

    private void startResearchService() {
        Intent serviceIntent = new Intent(this, LocationResearchService.class);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(serviceIntent);
        } else {
            startService(serviceIntent);
        }
    }
}