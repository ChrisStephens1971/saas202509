import React, { useState, useRef } from 'react'
import { Upload, X, CheckCircle, AlertCircle } from 'lucide-react'

interface ViolationPhotoUploadProps {
  violationId: string
  onUploadComplete: () => void
}

interface UploadedFile {
  file: File
  preview: string
  status: 'pending' | 'uploading' | 'success' | 'error'
  error?: string
  progress?: number
}

export default function ViolationPhotoUpload({ violationId, onUploadComplete }: ViolationPhotoUploadProps) {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const droppedFiles = Array.from(e.dataTransfer.files)
    handleFiles(droppedFiles)
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files)
      handleFiles(selectedFiles)
    }
  }

  const handleFiles = (newFiles: File[]) => {
    // Validate file types
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/heic']
    const validFiles = newFiles.filter(file => {
      if (!validTypes.includes(file.type)) {
        alert(`Invalid file type: ${file.name}. Only JPG, PNG, and HEIC are allowed.`)
        return false
      }
      if (file.size > 10 * 1024 * 1024) {
        alert(`File too large: ${file.name}. Maximum size is 10MB.`)
        return false
      }
      return true
    })

    // Create previews and add to state
    const uploadedFiles: UploadedFile[] = validFiles.map(file => ({
      file,
      preview: URL.createObjectURL(file),
      status: 'pending'
    }))

    setFiles(prev => [...prev, ...uploadedFiles])
  }

  const removeFile = (index: number) => {
    setFiles(prev => {
      const newFiles = [...prev]
      URL.revokeObjectURL(newFiles[index].preview)
      newFiles.splice(index, 1)
      return newFiles
    })
  }

  const uploadFile = async (index: number) => {
    const fileData = files[index]

    // Update status to uploading
    setFiles(prev => {
      const newFiles = [...prev]
      newFiles[index].status = 'uploading'
      newFiles[index].progress = 0
      return newFiles
    })

    const formData = new FormData()
    formData.append('photo', fileData.file)
    formData.append('violation_id', violationId)
    formData.append('caption', '')
    formData.append('taken_date', new Date().toISOString().split('T')[0])

    try {
      const token = localStorage.getItem('token')
      const response = await fetch('http://localhost:8009/api/v1/violation-photos/upload/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Upload failed')
      }

      // Update status to success
      setFiles(prev => {
        const newFiles = [...prev]
        newFiles[index].status = 'success'
        newFiles[index].progress = 100
        return newFiles
      })

      onUploadComplete()
    } catch (error) {
      // Update status to error
      setFiles(prev => {
        const newFiles = [...prev]
        newFiles[index].status = 'error'
        newFiles[index].error = error instanceof Error ? error.message : 'Upload failed'
        return newFiles
      })
    }
  }

  const uploadAllFiles = async () => {
    for (let i = 0; i < files.length; i++) {
      if (files[i].status === 'pending') {
        await uploadFile(i)
      }
    }
  }

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragging
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <Upload className="mx-auto h-12 w-12 text-gray-400" />
        <p className="mt-2 text-sm text-gray-600">
          Drag and drop photos here, or{' '}
          <button
            type="button"
            className="text-blue-600 hover:text-blue-500 font-medium"
            onClick={() => fileInputRef.current?.click()}
          >
            browse
          </button>
        </p>
        <p className="mt-1 text-xs text-gray-500">
          JPG, PNG, or HEIC up to 10MB
        </p>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept="image/jpeg,image/jpg,image/png,image/heic"
          multiple
          onChange={handleFileSelect}
        />
      </div>

      {/* File list with previews */}
      {files.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-gray-700">
              {files.length} {files.length === 1 ? 'photo' : 'photos'} selected
            </h4>
            <button
              onClick={uploadAllFiles}
              disabled={files.every(f => f.status !== 'pending')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-sm font-medium"
            >
              Upload All
            </button>
          </div>

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
            {files.map((fileData, index) => (
              <div
                key={index}
                className="relative group border rounded-lg overflow-hidden bg-white shadow-sm"
              >
                {/* Preview image */}
                <div className="aspect-square bg-gray-100">
                  <img
                    src={fileData.preview}
                    alt={fileData.file.name}
                    className="w-full h-full object-cover"
                  />
                </div>

                {/* Status overlay */}
                <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all">
                  {/* Remove button */}
                  {fileData.status === 'pending' && (
                    <button
                      onClick={() => removeFile(index)}
                      className="absolute top-2 right-2 p-1 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}

                  {/* Status indicator */}
                  <div className="absolute bottom-2 left-2 right-2">
                    {fileData.status === 'pending' && (
                      <button
                        onClick={() => uploadFile(index)}
                        className="w-full px-2 py-1 bg-blue-600 text-white rounded text-xs font-medium hover:bg-blue-700"
                      >
                        Upload
                      </button>
                    )}

                    {fileData.status === 'uploading' && (
                      <div className="bg-white rounded px-2 py-1">
                        <div className="flex items-center space-x-2">
                          <div className="flex-1 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full transition-all"
                              style={{ width: `${fileData.progress || 0}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-600">
                            {fileData.progress || 0}%
                          </span>
                        </div>
                      </div>
                    )}

                    {fileData.status === 'success' && (
                      <div className="flex items-center space-x-1 bg-green-100 text-green-800 rounded px-2 py-1">
                        <CheckCircle className="h-4 w-4" />
                        <span className="text-xs font-medium">Uploaded</span>
                      </div>
                    )}

                    {fileData.status === 'error' && (
                      <div className="bg-red-100 text-red-800 rounded px-2 py-1">
                        <div className="flex items-center space-x-1">
                          <AlertCircle className="h-4 w-4" />
                          <span className="text-xs font-medium">Failed</span>
                        </div>
                        <p className="text-xs mt-1">{fileData.error}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* File name */}
                <div className="p-2 border-t">
                  <p className="text-xs text-gray-600 truncate">
                    {fileData.file.name}
                  </p>
                  <p className="text-xs text-gray-400">
                    {(fileData.file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
