package com.example.marktan.asada_client;

import android.os.Bundle;
import java.util.*;
import android.support.v7.app.AppCompatActivity;
import android.support.v7.widget.Toolbar;
import com.github.mikephil.charting.charts.BarChart;
import com.github.mikephil.charting.data.BarDataSet;
import com.github.mikephil.charting.data.BarEntry;
import com.github.mikephil.charting.data.BarData;


public class AccountPage extends AppCompatActivity {

    BarChart barChart;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_account_page);
        Toolbar toolbar = (Toolbar) findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);

        barChart = (BarChart) findViewById(R.id.bargraph);
        ArrayList<BarEntry> entries = new ArrayList<>();
        entries.add(new BarEntry(10f,4));
        entries.add(new BarEntry(20f,2));
        entries.add(new BarEntry(30f,5));
        entries.add(new BarEntry(40f,3));
        BarDataSet bds = new BarDataSet(entries,"dates");

        BarData bd = new BarData(bds);
        barChart.setData(bd);
        barChart.setTouchEnabled(true);
        barChart.setDragEnabled(true);
        barChart.setScaleEnabled(true);
    }

}
